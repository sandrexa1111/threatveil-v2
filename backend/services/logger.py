"""Structured logging for ThreatVeilAI."""
import logging
import time
from typing import Any, Dict, Optional

# Configure structured logger
logger = logging.getLogger("threatveil")
logger.setLevel(logging.INFO)

# Create console handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)


def log_scan(
    domain: str,
    risk_score: int,
    duration_ms: float,
    signal_count: int,
    partial_failures: int,
    scan_id: str,
) -> None:
    """Log scan completion with structured data."""
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
        },
    )


def log_external_call(
    service: str,
    latency_ms: float,
    cache_hit: bool,
    success: bool,
    error: Optional[str] = None,
) -> None:
    """Log external service call with latency and cache status."""
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
        },
    )

