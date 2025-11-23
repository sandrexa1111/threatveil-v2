"""Structured logging configuration for ThreatVeil."""
import logging
import sys
from typing import Any, Dict, Optional

# Configure root logger
logger = logging.getLogger("threatveil")
logger.setLevel(logging.INFO)

# Console handler with structured format
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Structured format: timestamp, level, message, extra fields as JSON
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s | %(extra)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_scan(
    domain: str,
    risk_score: int,
    duration_ms: float,
    signal_count: int,
    partial_failures: int,
    scan_id: str,
    **kwargs: Any,
) -> None:
    """Log a completed scan with structured data."""
    level = logging.WARNING if partial_failures > 0 else logging.INFO
    logger.log(
        level,
        f"scan_complete domain={domain} risk_score={risk_score} duration_ms={duration_ms:.0f} "
        f"signals={signal_count} partial_failures={partial_failures} scan_id={scan_id}",
        extra={
            "event": "scan_complete",
            "domain": domain,
            "risk_score": risk_score,
            "duration_ms": duration_ms,
            "signal_count": signal_count,
            "partial_failures": partial_failures,
            "scan_id": scan_id,
            **kwargs,
        },
    )


def log_service_call(
    service: str,
    latency_ms: float,
    cache_hit: bool = False,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log an external service call with metrics."""
    level = logging.ERROR if not success else logging.INFO
    cache_status = "hit" if cache_hit else "miss"
    msg = f"external_call service={service} latency_ms={latency_ms:.0f} cache={cache_status} success={success}"
    if error:
        msg += f" error={error}"
    
    logger.log(
        level,
        msg,
        extra={
            "event": "external_call",
            "service": service,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
            "success": success,
            "error": error,
            **kwargs,
        },
    )

