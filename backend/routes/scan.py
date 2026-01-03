import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..db import get_session as get_cache_session
from ..models import Organization, Scan as ScanModel, ScanAI
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
    with get_cache_session() as session:
        return await cached_signal_bundle(
            session,
            "nvd",
            {"tokens": tokens},
            60 * 60 * 24,
            lambda: cve_service.fetch_cves(tokens),
        )


async def _safe_fetch_dns(domain: str) -> Tuple[dict, List[Signal]]:
    try:
        return await dns_service.fetch_dns_metadata(domain)
    except Exception as e:
        return {}, [
            make_service_error_signal(service_name="DNS", error=e, category="network")
        ]


async def _safe_fetch_http(domain: str) -> Tuple[dict, List[Signal], List[str]]:
    try:
        return await http_service.fetch_http_metadata(domain)
    except Exception as e:
        return {}, [
            make_service_error_signal(service_name="HTTP", error=e, category="network")
        ], []


async def _safe_fetch_tls(domain: str) -> Tuple[dict, List[Signal]]:
    try:
        return await tls_service.fetch_tls_metadata(domain)
    except Exception as e:
        return {}, [
            make_service_error_signal(service_name="TLS", error=e, category="network")
        ]


async def _safe_fetch_ct(domain: str) -> Tuple[dict, List[Signal]]:
    try:
        return await _cached_ct(domain)
    except Exception as e:
        return {}, [
            make_service_error_signal(service_name="CT", error=e, category="network")
        ]


async def _safe_fetch_otx(domain: str) -> Tuple[dict, List[Signal]]:
    try:
        return await otx_service.fetch_otx_indicators(domain)
    except Exception as e:
        return {}, [
            make_service_error_signal(service_name="OTX", error=e, category="network")
        ]


async def _safe_fetch_cves(tokens: List[str]) -> Tuple[List[dict], List[Signal]]:
    if not tokens:
        return [], []
    try:
        return await _cached_cves(tokens)
    except Exception as e:
        return [], [
            make_service_error_signal(service_name="CVE", error=e, category="software")
        ]


async def _safe_fetch_github(org: str) -> Tuple[List[dict], List[Signal]]:
    if not org:
        return [], []
    try:
        return await github_service.search_code_leaks(org)
    except Exception as e:
        return [], [
            make_service_error_signal(
                service_name="GitHub", error=e, category="ai_integration"
            )
        ]


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

    # Get or create Organization for this domain
    normalized_domain = domain.lower().strip()
    org = db.query(Organization).filter(Organization.primary_domain == normalized_domain).first()
    if not org:
        org = Organization(
            id=str(uuid.uuid4()),
            primary_domain=normalized_domain,
            name=None,  # Can be set later via API or admin
        )
        db.add(org)
        db.flush()  # Flush to get org.id before using it

    # Persist to database
    # Note: get_db() context manager will auto-commit on successful exit
    # We catch exceptions here to prevent the request from failing if DB write fails
    try:
        scan_model = ScanModel(
            id=scan_id,
            domain=domain,
            github_org=payload.github_org,
            risk_score=risk_score,
            risk_likelihood_30d=result.breach_likelihood_30d,
            risk_likelihood_90d=result.breach_likelihood_90d,
            categories_json={k: v.model_dump(mode="json") for k, v in categories.items()},
            signals_json=[signal.model_dump(mode="json") for signal in all_signals],
            summary=summary,
            org_id=org.id,  # Link scan to organization
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
        db.add(scan_model)
        # Flush to ensure the object is in the session, commit happens via context manager
        db.flush()
        
        # Perform AI scan and create ScanAI record (Horizon Phase 1)
        try:
            from ..services.ai.ai_scan_service import ai_scan_for_scan
            await ai_scan_for_scan(scan_model, db)
        except Exception as ai_error:
            # Log AI scan error but don't fail the main scan
            # The scan will still return successfully
            pass
        
        # Auto-verify resolved decisions (Phase 3)
        try:
            from ..services.verification_service import auto_verify_decisions_for_scan
            verified_ids = auto_verify_decisions_for_scan(db, scan_model)
            if verified_ids:
                # Decisions were auto-verified - log this
                pass
        except Exception:
            # Never fail the scan if verification fails
            pass
        
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


@router.get("/{scan_id}")
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Get scan details by ID.
    Returns 404 if scan doesn't exist.
    """
    scan = db.query(ScanModel).filter(ScanModel.id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Reconstruct signals from JSON
    signals = [Signal(**signal_data) for signal_data in scan.signals_json]
    
    # Reconstruct categories from JSON
    from ..schemas import CategoryScore
    categories = {k: CategoryScore(**v) for k, v in scan.categories_json.items()}
    
    result = ScanResult(
        id=scan.id,
        domain=scan.domain,
        github_org=scan.github_org,
        risk_score=scan.risk_score,
        categories=categories,
        signals=signals,
        summary=scan.summary,
        breach_likelihood_30d=scan.risk_likelihood_30d,
        breach_likelihood_90d=scan.risk_likelihood_90d,
        created_at=scan.created_at,
    )
    
    return ScanResponse(result=result)


@router.get("/{scan_id}/ai")
async def get_scan_ai(scan_id: str, db: Session = Depends(get_db)):
    """
    Get AI risk data for a scan.
    Returns 404 if ScanAI record doesn't exist yet.
    """
    scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan_id).first()
    
    if not scan_ai:
        raise HTTPException(status_code=404, detail="AI scan data not available for this scan")
    
    # Extract tools, agents, and keys from the JSON fields
    ai_tools = scan_ai.ai_tools or []
    ai_keys = scan_ai.ai_keys or []
    
    # Extract agent frameworks from ai_tools (tools that suggest agent usage)
    agent_keywords = ["langchain", "crewai", "autogen", "langgraph", "agent"]
    ai_agents = [tool for tool in ai_tools if any(keyword in tool.lower() for keyword in agent_keywords)]
    
    return {
        "ai_score": scan_ai.ai_score or 0,
        "ai_tools_detected": ai_tools,
        "ai_key_leaks": ai_keys,
        "ai_agents_detected": ai_agents,
        "ai_summary": scan_ai.ai_summary or "",
        "created_at": scan_ai.created_at.isoformat() if scan_ai.created_at else None,
    }


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Delete a scan by ID.
    Returns 404 if scan doesn't exist.
    """
    # Check if scan exists
    scan = db.query(ScanModel).filter(ScanModel.id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete the scan - cascade will handle signals
    db.delete(scan)
    # Commit happens automatically via get_db dependency if no exception raised
    # but we can explicit commit to be sure before returning
    db.commit()
    
    return None


@router.get("/{scan_id}/previous")
async def get_previous_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Get the previous scan for the same domain.
    Used for calculating risk trend.
    Returns null score if no previous scan exists.
    """
    # First get the current scan to find the domain
    current_scan = db.query(ScanModel).filter(ScanModel.id == scan_id).first()
    if not current_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Find the most recent scan for this domain that's older than the current one
    previous_scan = db.query(ScanModel).filter(
        ScanModel.domain == current_scan.domain,
        ScanModel.created_at < current_scan.created_at
    ).order_by(ScanModel.created_at.desc()).first()
    
    if not previous_scan:
        return {"previous_score": None, "previous_scan_id": None}
    
    return {
        "previous_score": previous_scan.risk_score,
        "previous_scan_id": previous_scan.id,
        "previous_created_at": previous_scan.created_at.isoformat() if previous_scan.created_at else None
    }
