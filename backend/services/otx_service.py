import time
from typing import Dict, List, Tuple

import httpx

from ..config import settings
from ..logging_config import log_service_call
from ..schemas import Signal
from .signal_factory import make_signal, make_service_error_signal
from .utils import with_backoff

BASE_URL = "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general"
TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)


async def fetch_otx(domain: str) -> Tuple[Dict, List[Signal]]:
    """Fetch threat intelligence from AlienVault OTX for a domain."""
    if not settings.otx_api_key:
        return {}, [
            make_service_error_signal(
                service_name="OTX",
                error=Exception("OTX_API_KEY not configured"),
                category="network",
            )
        ]

    start_time = time.time()
    headers = {"X-OTX-API-KEY": settings.otx_api_key}
    url = BASE_URL.format(domain=domain)
    metadata: Dict = {}
    signals: List[Signal] = []

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.get(url, headers=headers),
                retries=3,
                base_delay=0.2,
                max_delay=2.5,
            )
            latency_ms = (time.time() - start_time) * 1000
            response.raise_for_status()
            metadata = response.json()
            pulse_info = metadata.get("pulse_info", {})
            pulse_count = pulse_info.get("count", 0)

            if pulse_count > 0:
                # Generate threat context signals
                severity = "medium" if pulse_count > 5 else "low"
                signals.append(
                    make_signal(
                        signal_id="otx_pulse_match",
                        signal_type="otx",
                        detail=f"Domain seen in {pulse_count} threat intelligence pulse(s)",
                        severity=severity,
                        category="network",
                        source="otx",
                        url=url,
                        raw={"pulse_count": pulse_count, "pulses": pulse_info.get("pulses", [])[:3]},
                    )
                )

            log_service_call(
                service="otx",
                latency_ms=latency_ms,
                cache_hit=False,
                success=True,
            )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="otx",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        signals.append(
            make_service_error_signal(
                service_name="OTX",
                error=e,
                category="network",
            )
        )

    return metadata, signals
