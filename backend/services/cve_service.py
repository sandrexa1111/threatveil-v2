"""CVE Service using NVD (National Vulnerability Database) API.

This module fetches CVE vulnerabilities from NIST's NVD API based on
technology/software tokens detected during scans.
"""
import asyncio
import time
from typing import Dict, List, Tuple

import httpx

from ..logging_config import log_service_call
from ..schemas import Signal
from .signal_factory import make_signal, make_service_error_signal
from .utils import with_backoff

# NVD API v2.0 endpoint
BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
TIMEOUT = httpx.Timeout(30.0, connect=10.0, read=20.0)


def _severity_from_cvss(score: float) -> str:
    """Map CVSS score to severity level."""
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def _extract_cvss_score(cve_item: Dict) -> float:
    """Extract the highest CVSS score from a CVE item.
    
    NVD provides CVSS v3.1, v3.0, and v2.0 scores. We prefer v3.1 > v3.0 > v2.0.
    """
    metrics = cve_item.get("metrics", {})
    
    # Try CVSS v3.1 first
    cvss_v31 = metrics.get("cvssMetricV31", [])
    if cvss_v31:
        for metric in cvss_v31:
            cvss_data = metric.get("cvssData", {})
            if "baseScore" in cvss_data:
                return float(cvss_data["baseScore"])
    
    # Try CVSS v3.0
    cvss_v30 = metrics.get("cvssMetricV30", [])
    if cvss_v30:
        for metric in cvss_v30:
            cvss_data = metric.get("cvssData", {})
            if "baseScore" in cvss_data:
                return float(cvss_data["baseScore"])
    
    # Fall back to CVSS v2.0
    cvss_v2 = metrics.get("cvssMetricV2", [])
    if cvss_v2:
        for metric in cvss_v2:
            cvss_data = metric.get("cvssData", {})
            if "baseScore" in cvss_data:
                return float(cvss_data["baseScore"])
    
    return 0.0


def _get_description(cve_item: Dict) -> str:
    """Extract English description from CVE item."""
    descriptions = cve_item.get("descriptions", [])
    for desc in descriptions:
        if desc.get("lang") == "en":
            return desc.get("value", "")
    # Fallback to first description if no English found
    if descriptions:
        return descriptions[0].get("value", "")
    return ""


async def fetch_cves(tokens: List[str]) -> Tuple[List[Dict], List[Signal]]:
    """Fetch CVEs from NVD API for given tech tokens.
    
    Args:
        tokens: List of technology/software names to search for (e.g., ["nginx", "apache"])
    
    Returns:
        Tuple of (list of CVE dicts, list of Signal objects)
    """
    if not tokens:
        return [], []

    start_time = time.time()
    cves: List[Dict] = []
    signals: List[Signal] = []
    seen_cve_ids = set()

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Search for CVEs for each token (limit to first 3 tokens to avoid rate limiting)
            for token in tokens[:3]:
                # NVD API uses keywordSearch parameter
                params = {
                    "keywordSearch": token,
                    "resultsPerPage": 5,  # Limit results per token
                }
                
                response = await with_backoff(
                    lambda p=params: client.get(BASE_URL, params=p),
                    retries=3,
                    base_delay=0.5,
                    max_delay=5.0,
                )
                response.raise_for_status()
                data = response.json()
                
                vulnerabilities = data.get("vulnerabilities", [])
                
                for vuln in vulnerabilities:
                    cve_item = vuln.get("cve", {})
                    cve_id = cve_item.get("id", "")
                    
                    if not cve_id or cve_id in seen_cve_ids:
                        continue
                    seen_cve_ids.add(cve_id)
                    
                    score = _extract_cvss_score(cve_item)
                    severity = _severity_from_cvss(score)
                    description = _get_description(cve_item)
                    published = cve_item.get("published", "")
                    
                    # Build NVD URL for the CVE
                    nvd_url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
                    
                    cve = {
                        "id": cve_id,
                        "title": description[:200] + "..." if len(description) > 200 else description,
                        "score": score,
                        "severity": severity,
                        "href": nvd_url,
                        "published": published,
                    }
                    cves.append(cve)
                    
                    # Only create signals for CVEs with meaningful scores
                    if score > 0:
                        signals.append(
                            make_signal(
                                signal_id=f"cve_{cve_id}",
                                signal_type="cve",
                                detail=f"{cve_id}: {description[:100]}{'...' if len(description) > 100 else ''} (CVSS {score:.1f})",
                                severity=severity,
                                category="software",
                                source="nvd",
                                url=nvd_url,
                                raw=cve,
                            )
                        )
                
                # Small delay between requests to respect NVD rate limits
                # NVD allows 5 requests per 30 seconds without API key
                await asyncio.sleep(0.5)

        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="nvd",
            latency_ms=latency_ms,
            cache_hit=False,
            success=True,
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="nvd",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        signals.append(
            make_service_error_signal(
                service_name="NVD",
                error=e,
                category="software",
            )
        )

    return cves, signals



