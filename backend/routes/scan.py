import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..db import get_session as get_cache_session
from ..models import Scan as ScanModel
from ..schemas import ScanRequest, ScanResponse, ScanResult, Signal
from ..scoring import score_signals
from ..security import enforce_rate_limit
from ..services import (
    ctlog_service,
    cve_service,
    dns_service,
    github_service,
    http_service,
    llm_service,
    ml_service,
    otx_service,
    tls_service,
)
from ..services.cache import cached_signal_bundle
from ..logging_config import log_scan
from ..services.signal_factory import make_signal, make_service_error_signal

router = APIRouter(prefix="/api/v1/scan", tags=["scan"])


async def _cached_ct(domain: str) -> Tuple[dict, List[Signal]]:
    with get_cache_session() as session:
        return await cached_signal_bundle(
            session,
            "ctlog",
            {"domain": domain},
            60 * 60 * 24,
            lambda: ctlog_service.fetch_ct_logs(domain),
        )


async def _cached_cves(tokens: List[str]) -> Tuple[List[dict], List[Signal]]:
    if not tokens:
        return [], []

    async def fetch():
        cves, signals = await cve_service.fetch_cves(tokens)
        return {"cves": cves}, signals

    with get_cache_session() as session:
        metadata, signals = await cached_signal_bundle(
            session,
            "cve",
            {"tokens": sorted(tokens)},
            60 * 60 * 24,
            fetch,
        )
    return metadata.get("cves", []), signals


async def _cached_github(org: str) -> Tuple[List[dict], List[Signal]]:
    if not org:
        return [], []

    async def fetch():
        leaks, signals = await github_service.search_code_leaks(org)
        return {"leaks": leaks}, signals

    with get_cache_session() as session:
        metadata, signals = await cached_signal_bundle(
            session,
            "github",
            {"org": org},
            60 * 60 * 24,
            fetch,
        )
    return metadata.get("leaks", []), signals


async def _safe_fetch_dns(domain: str) -> Tuple[dict, List[Signal]]:
    """Safely fetch DNS metadata, returning empty results on failure."""
    try:
        return await dns_service.fetch_dns_metadata(domain)
    except Exception as e:
        return (
            {"error": str(e)},
            [make_service_error_signal(service_name="DNS", error=e, category="network")],
        )


async def _safe_fetch_http(domain: str) -> Tuple[dict, List[Signal], List[str]]:
    """Safely fetch HTTP metadata, returning empty results on failure."""
    try:
        return await http_service.fetch_http_metadata(domain)
    except Exception as e:
        return (
            {"error": str(e)},
            [make_service_error_signal(service_name="HTTP", error=e, category="network")],
            [],
        )


async def _safe_fetch_tls(domain: str) -> Tuple[dict, List[Signal]]:
    """Safely fetch TLS metadata, returning empty results on failure."""
    try:
        return await tls_service.fetch_tls_metadata(domain)
    except Exception as e:
        return (
            {"error": str(e)},
            [make_service_error_signal(service_name="TLS", error=e, category="network")],
        )


async def _safe_fetch_ct(domain: str) -> Tuple[dict, List[Signal]]:
    """Safely fetch CT log metadata, returning empty results on failure."""
    try:
        return await _cached_ct(domain)
    except Exception as e:
        return (
            {"error": str(e)},
            [make_service_error_signal(service_name="CT", error=e, category="data_exposure")],
        )


async def _safe_fetch_otx(domain: str) -> Tuple[dict, List[Signal]]:
    """Safely fetch OTX metadata, returning empty results on failure."""
    try:
        return await otx_service.fetch_otx(domain)
    except Exception as e:
        return (
            {"error": str(e)},
            [make_service_error_signal(service_name="OTX", error=e, category="network")],
        )


async def _safe_fetch_cves(tokens: List[str]) -> Tuple[List[dict], List[Signal]]:
    """Safely fetch CVE data, returning empty results on failure."""
    if not tokens:
        return [], []
    try:
        return await _cached_cves(tokens)
    except Exception as e:
        return (
            [],
            [make_service_error_signal(service_name="CVE", error=e, category="software")],
        )


async def _safe_fetch_github(org: str) -> Tuple[List[dict], List[Signal]]:
    """Safely fetch GitHub data, returning empty results on failure."""
    if not org:
        return [], []
    try:
        return await _cached_github(org)
    except Exception as e:
        return (
            [],
            [make_service_error_signal(service_name="GitHub", error=e, category="ai_integration")],
        )


@router.post(
    "/vendor",
    response_model=ScanResponse,
    dependencies=[Depends(enforce_rate_limit)],
)
async def scan_vendor(payload: ScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    start_time = time.time()
    domain = payload.domain.strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")

    # Run all parallel tasks with error handling
    dns_result, http_result, tls_result, ct_result, otx_result = await asyncio.gather(
        _safe_fetch_dns(domain),
        _safe_fetch_http(domain),
        _safe_fetch_tls(domain),
        _safe_fetch_ct(domain),
        _safe_fetch_otx(domain),
        return_exceptions=False,  # Our safe wrappers handle exceptions
    )

    dns_metadata, dns_signals = dns_result
    http_metadata, http_signals, tech_tokens = http_result
    tls_metadata, tls_signals = tls_result
    ct_metadata, ct_signals = ct_result
    otx_metadata, otx_signals = otx_result

    # Fetch dependent services
    cves, cve_signals = await _safe_fetch_cves(tech_tokens)
    github_leaks, github_signals = await _safe_fetch_github(payload.github_org or "")

    all_signals: List[Signal] = [
        *dns_signals,
        *http_signals,
        *tls_signals,
        *ct_signals,
        *cve_signals,
        *github_signals,
        *otx_signals,
    ]
    
    # Count partial failures (service error signals)
    partial_failures = sum(1 for s in all_signals if s.id.startswith("service_") and s.id.endswith("_failure"))

    if not all_signals:
        all_signals.append(
            make_signal(
                signal_id="scan_completed_no_findings",
                signal_type="ai_guard",
                detail="Scan completed with no critical findings",
                severity="low",
                category="software",
                source="system",
                raw={},
            )
        )

    risk_score, categories = score_signals(all_signals)
    likelihoods = ml_service.estimate_likelihoods(all_signals)
    
    # Safely get summary with fallback
    try:
        summary = await llm_service.summarize(db, all_signals, risk_score, likelihoods)
    except Exception as e:
        # Fallback summary if LLM service fails
        summary = llm_service.fallback_summary(all_signals, risk_score, likelihoods)

    scan_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    result = ScanResult(
        id=scan_id,
        domain=domain,
        github_org=payload.github_org,
        risk_score=risk_score,
        categories=categories,
        signals=all_signals,
        summary=summary,
        breach_likelihood_30d=likelihoods["breach_likelihood_30d"],
        breach_likelihood_90d=likelihoods["breach_likelihood_90d"],
        created_at=created_at,
    )

    # Persist to database
    # Note: get_db() context manager will auto-commit on successful exit
    # We catch exceptions here to prevent the request from failing if DB write fails
    try:
        db.add(
            ScanModel(
                id=scan_id,
                domain=domain,
                github_org=payload.github_org,
                risk_score=risk_score,
                risk_likelihood_30d=result.breach_likelihood_30d,
                risk_likelihood_90d=result.breach_likelihood_90d,
                categories_json={k: v.model_dump(mode="json") for k, v in categories.items()},
                signals_json=[signal.model_dump(mode="json") for signal in all_signals],
                summary=summary,
                raw_payload={
                    "dns": dns_metadata,
                    "http": http_metadata,
                    "tls": tls_metadata,
                    "ct": ct_metadata,
                    "cves": cves,
                    "github": github_leaks,
                    "otx": otx_metadata,
                },
            )
        )
        # Flush to ensure the object is in the session, commit happens via context manager
        db.flush()
    except Exception:
        # Rollback on error - context manager will handle cleanup
        db.rollback()
        # Log error but don't fail the request - return partial results
        # In production, you'd want to log this properly (e.g., using logging module)

    # Log scan completion
    duration_ms = (time.time() - start_time) * 1000
    log_scan(
        domain=domain,
        risk_score=risk_score,
        duration_ms=duration_ms,
        signal_count=len(all_signals),
        partial_failures=partial_failures,
        scan_id=scan_id,
    )

    return ScanResponse(result=result)
