from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..schemas import Category, Evidence, Severity, Signal, SignalType


def make_signal(
    *,
    signal_id: str,
    signal_type: SignalType,
    detail: str,
    severity: Severity,
    category: Category,
    source: str,
    url: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> Signal:
    return Signal(
        id=signal_id,
        type=signal_type,
        detail=detail,
        severity=severity,
        category=category,
        evidence=Evidence(
            source=source,
            observed_at=datetime.now(timezone.utc),
            url=url,
            raw=raw or {},
        ),
    )


def make_service_error_signal(
    *,
    service_name: str,
    error: Exception,
    category: Category = "network",
) -> Signal:
    """Create a standardized service error signal for user-friendly error reporting."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # User-friendly messages
    friendly_messages = {
        "DNS": "DNS lookup failed, results may be incomplete.",
        "HTTP": "HTTP security check failed, results may be incomplete.",
        "TLS": "TLS certificate check failed, results may be incomplete.",
        "CT": "Certificate transparency log check failed, results may be incomplete.",
        "OTX": "Threat intelligence enrichment unavailable, results may be incomplete.",
        "CVE": "Vulnerability database check failed, results may be incomplete.",
        "NVD": "NVD vulnerability database check failed, results may be incomplete.",
        "GitHub": "GitHub code search unavailable, results may be incomplete.",
    }
    
    detail = friendly_messages.get(service_name, f"{service_name} service failed, results may be incomplete.")
    
    return make_signal(
        signal_id=f"service_{service_name.lower()}_failure",
        signal_type="ai_guard",  # Use ai_guard for service errors to distinguish from actual findings
        detail=detail,
        severity="low",
        category=category,
        source=service_name.lower(),
        raw={
            "error": error_msg,
            "error_type": error_type,
            "service": service_name,
        },
    )
