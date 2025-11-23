import time
from typing import Dict, List, Tuple

import httpx

from ..config import settings
from ..logging_config import log_service_call
from ..schemas import Signal
from .signal_factory import make_signal, make_service_error_signal
from .utils import with_backoff

BASE_URL = "https://vulners.com/api/v3/search/lucene/"
TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)


def _severity_from_cvss(score: float) -> str:
    """Map CVSS score to severity level."""
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


async def fetch_cves(tokens: List[str]) -> Tuple[List[Dict], List[Signal]]:
    """Fetch CVEs from Vulners API for given tech tokens."""
    if not tokens:
        return [], []

    if not settings.vulners_api_key:
        return [], [
            make_service_error_signal(
                service_name="Vulners",
                error=Exception("VULNERS_API_KEY not configured"),
                category="software",
            )
        ]

    start_time = time.time()
    # Build query: search for each token with type:cve filter
    queries = [f'"{token}" AND type:cve' for token in tokens[:5]]  # Limit to 5 tokens
    query = " OR ".join(queries)
    payload = {"query": query, "size": 10}
    headers = {"X-Vulners-Api-Key": settings.vulners_api_key}
    cves: List[Dict] = []
    signals: List[Signal] = []
    seen_cve_ids = set()

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.post(BASE_URL, json=payload, headers=headers),
                retries=3,
                base_delay=0.2,
                max_delay=2.5,
            )
            latency_ms = (time.time() - start_time) * 1000
            response.raise_for_status()
            data = response.json()
            results = data.get("data", {}).get("search", [])

            for result in results:
                source = result.get("_source", {})
                cve_id = source.get("id", "")
                if not cve_id or cve_id in seen_cve_ids:
                    continue
                seen_cve_ids.add(cve_id)

                cvss = source.get("cvss", {})
                score = float(cvss.get("score", 0))
                severity = _severity_from_cvss(score)
                cve = {
                    "id": cve_id,
                    "title": source.get("title", ""),
                    "score": score,
                    "severity": severity,
                    "href": source.get("href", ""),
                    "published": source.get("published", ""),
                }
                cves.append(cve)
                signals.append(
                    make_signal(
                        signal_id=f"cve_{cve_id}",
                        signal_type="cve",
                        detail=f"{cve_id}: {source.get('title', 'Unknown vulnerability')} (CVSS {score:.1f})",
                        severity=severity,
                        category="software",
                        source="vulners",
                        url=source.get("href"),
                        raw=cve,
                    )
                )

            log_service_call(
                service="vulners",
                latency_ms=latency_ms,
                cache_hit=False,
                success=True,
            )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="vulners",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        signals.append(
            make_service_error_signal(
                service_name="Vulners",
                error=e,
                category="software",
            )
        )

    return cves, signals
