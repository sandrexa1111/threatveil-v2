import time
from typing import Dict, List, Tuple

import httpx

from ..config import settings
from ..logging_config import log_service_call
from ..schemas import Signal
from .signal_factory import make_signal, make_service_error_signal
from .utils import with_backoff

TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)
SEARCH_URL = "https://api.github.com/search/code"


def _build_query(org: str) -> str:
    patterns = [
        'filename:.env',
        '"OPENAI_API_KEY"',
        '"GEMINI_API_KEY"',
        '"system prompt"',
        '"-----BEGIN PRIVATE KEY-----"',
    ]
    return f"org:{org} " + " OR ".join(patterns)


async def search_code_leaks(github_org: str) -> Tuple[List[Dict], List[Signal]]:
    """Search GitHub for potential secret leaks in public repositories."""
    if not github_org:
        return [], []

    if not settings.github_token:
        return [], [
            make_service_error_signal(
                service_name="GitHub",
                error=Exception("GITHUB_TOKEN not configured"),
                category="ai_integration",
            )
        ]

    start_time = time.time()
    params = {"q": _build_query(github_org), "per_page": 10}
    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.get(SEARCH_URL, params=params, headers=headers),
                retries=3,
                base_delay=0.2,
                max_delay=2.5,
            )
            latency_ms = (time.time() - start_time) * 1000

            # Check rate limits
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            if rate_limit_remaining == "0":
                log_service_call(
                    service="github",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=False,
                    error="Rate limit exceeded",
                )

            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            signals: List[Signal] = []
            leak_metadata: List[Dict] = []

            for item in items:
                leak = {
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "repository": item.get("repository", {}).get("full_name"),
                    "html_url": item.get("html_url"),
                }
                leak_metadata.append(leak)

                # Determine severity based on file type
                path_lower = leak["path"].lower()
                if ".env" in path_lower or "private key" in path_lower:
                    severity = "high"
                    category = "data_exposure"
                else:
                    severity = "medium"
                    category = "ai_integration"

                signals.append(
                    make_signal(
                        signal_id=f"github_leak_{leak['repository']}_{leak['path']}",
                        signal_type="github",
                        detail=f"Potential secret exposure in {leak['repository']}/{leak['path']}",
                        severity=severity,
                        category=category,
                        source="github",
                        url=leak["html_url"],
                        raw=leak,
                    )
                )

            log_service_call(
                service="github",
                latency_ms=latency_ms,
                cache_hit=False,
                success=True,
            )
            return leak_metadata, signals

    except httpx.HTTPStatusError as exc:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = f"HTTP {exc.response.status_code}"
        if exc.response.status_code == 403:
            error_msg = "Rate limit exceeded or access denied"
        log_service_call(
            service="github",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=error_msg,
        )
        return [], [
            make_service_error_signal(
                service_name="GitHub",
                error=exc,
                category="ai_integration",
            )
        ]
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="github",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        return [], [
            make_service_error_signal(
                service_name="GitHub",
                error=e,
                category="ai_integration",
            )
        ]
