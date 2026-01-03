"""
Signal Normalizer Service

Converts raw findings from various sources into canonical Signal objects.
Each function produces a SignalCreate schema that can be persisted to the database.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models import Signal
from backend.schemas import EvidenceEnvelope, SignalCreate, Severity


def _make_evidence_envelope(
    source_service: str,
    raw: Dict[str, Any],
    detection_method: str = "rule",
    confidence: float = 0.8,
    external_refs: Optional[List[str]] = None,
    notes_for_ai: Optional[str] = None,
) -> EvidenceEnvelope:
    """Create a standardized evidence envelope."""
    return EvidenceEnvelope(
        source_service=source_service,
        observed_at=datetime.now(timezone.utc),
        raw=raw,
        external_refs=external_refs or [],
        detection_method=detection_method,
        confidence=confidence,
        notes_for_ai=notes_for_ai,
    )


def create_canonical_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    source: str,
    signal_type: str,
    severity: Severity,
    category: str,
    title: str,
    detail: str,
    evidence: EvidenceEnvelope,
) -> Signal:
    """
    Create and persist a canonical signal to the database.
    
    Args:
        db: Database session
        org_id: Organization ID
        scan_id: Optional scan ID
        asset_id: Optional asset ID
        source: Signal source (e.g., 'threatveil_external', 'github')
        signal_type: Signal type (e.g., 'config', 'cve', 'secret')
        severity: Signal severity
        category: Signal category
        title: Short signal title
        detail: Detailed description
        evidence: Evidence envelope
        
    Returns:
        Persisted Signal instance
    """
    signal = Signal(
        id=str(uuid.uuid4()),
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source=source,
        type=signal_type,
        severity=severity,
        category=category,
        title=title,
        detail=detail,
        evidence=evidence.model_dump(mode="json"),
    )
    db.add(signal)
    db.flush()
    return signal


# =============================================================================
# HTTP/TLS Signal Converters
# =============================================================================

def hsts_missing_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    raw_headers: Dict[str, Any],
) -> Signal:
    """Convert missing HSTS finding to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="threatveil_external",
        signal_type="config",
        severity="medium",
        category="infrastructure",
        title="Missing HSTS Header",
        detail=f"The domain {domain} does not set the Strict-Transport-Security header, leaving it vulnerable to protocol downgrade attacks.",
        evidence=_make_evidence_envelope(
            source_service="http_service",
            raw=raw_headers,
            confidence=0.95,
            notes_for_ai="Missing HSTS header on HTTPS endpoint",
            external_refs=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"],
        ),
    )


def missing_csp_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    raw_headers: Dict[str, Any],
) -> Signal:
    """Convert missing CSP finding to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="threatveil_external",
        signal_type="config",
        severity="medium",
        category="infrastructure",
        title="Missing Content Security Policy",
        detail=f"The domain {domain} does not set a Content-Security-Policy header, increasing XSS attack risk.",
        evidence=_make_evidence_envelope(
            source_service="http_service",
            raw=raw_headers,
            confidence=0.9,
            notes_for_ai="No CSP header detected",
            external_refs=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP"],
        ),
    )


def tls_expiry_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    days_until_expiry: int,
    cert_info: Dict[str, Any],
) -> Signal:
    """Convert TLS certificate expiry warning to a canonical signal."""
    if days_until_expiry <= 0:
        severity = "critical"
        title = "TLS Certificate Expired"
        detail = f"The TLS certificate for {domain} has expired."
    elif days_until_expiry <= 7:
        severity = "high"
        title = "TLS Certificate Expiring Soon"
        detail = f"The TLS certificate for {domain} expires in {days_until_expiry} days."
    elif days_until_expiry <= 30:
        severity = "medium"
        title = "TLS Certificate Expiring"
        detail = f"The TLS certificate for {domain} expires in {days_until_expiry} days."
    else:
        severity = "low"
        title = "TLS Certificate Expiry Notice"
        detail = f"The TLS certificate for {domain} expires in {days_until_expiry} days."
    
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="threatveil_external",
        signal_type="config",
        severity=severity,
        category="infrastructure",
        title=title,
        detail=detail,
        evidence=_make_evidence_envelope(
            source_service="tls_service",
            raw={"days_until_expiry": days_until_expiry, **cert_info},
            confidence=1.0,
            notes_for_ai=f"Certificate expires in {days_until_expiry} days",
        ),
    )


def tls_weak_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    issue: str,
    raw_tls: Dict[str, Any],
) -> Signal:
    """Convert weak TLS configuration finding to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="threatveil_external",
        signal_type="config",
        severity="high",
        category="infrastructure",
        title="Weak TLS Configuration",
        detail=f"The domain {domain} has a weak TLS configuration: {issue}",
        evidence=_make_evidence_envelope(
            source_service="tls_service",
            raw=raw_tls,
            confidence=0.9,
            notes_for_ai=issue,
        ),
    )


# =============================================================================
# DNS Signal Converters
# =============================================================================

def dns_issue_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    issue_type: str,
    detail: str,
    raw_dns: Dict[str, Any],
    severity: Severity = "medium",
) -> Signal:
    """Convert DNS configuration issue to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="threatveil_external",
        signal_type="network",
        severity=severity,
        category="infrastructure",
        title=f"DNS Issue: {issue_type}",
        detail=detail,
        evidence=_make_evidence_envelope(
            source_service="dns_service",
            raw=raw_dns,
            confidence=0.85,
            notes_for_ai=issue_type,
        ),
    )


# =============================================================================
# CVE/Vulnerability Signal Converters
# =============================================================================

def cve_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    cve_id: str,
    cvss_score: float,
    description: str,
    affected_software: str,
    raw_cve: Dict[str, Any],
) -> Signal:
    """Convert CVE finding to a canonical signal."""
    # Determine severity from CVSS score
    if cvss_score >= 9.0:
        severity = "critical"
    elif cvss_score >= 7.0:
        severity = "high"
    elif cvss_score >= 4.0:
        severity = "medium"
    else:
        severity = "low"
    
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="nvd",
        signal_type="cve",
        severity=severity,
        category="software",
        title=f"{cve_id}: {affected_software}",
        detail=description,
        evidence=_make_evidence_envelope(
            source_service="nvd_service",
            raw=raw_cve,
            confidence=0.95,
            notes_for_ai=f"CVSS {cvss_score} vulnerability in {affected_software}",
            external_refs=[f"https://nvd.nist.gov/vuln/detail/{cve_id}"],
        ),
    )


# =============================================================================
# Threat Intelligence Signal Converters
# =============================================================================

def otx_pulse_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    domain: str,
    pulse_name: str,
    pulse_description: str,
    indicator_type: str,
    raw_otx: Dict[str, Any],
) -> Signal:
    """Convert OTX pulse finding to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="otx",
        signal_type="network",
        severity="medium",
        category="infrastructure",
        title=f"Threat Intel: {pulse_name}",
        detail=f"Domain {domain} appears in threat intelligence feed: {pulse_description}",
        evidence=_make_evidence_envelope(
            source_service="otx_service",
            raw=raw_otx,
            confidence=0.7,
            notes_for_ai=f"OTX indicator type: {indicator_type}",
            external_refs=["https://otx.alienvault.com/"],
        ),
    )


# =============================================================================
# GitHub/Code Signal Converters
# =============================================================================

def github_key_leak_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    key_type: str,
    repository: str,
    file_path: str,
    raw_leak: Dict[str, Any],
) -> Signal:
    """Convert GitHub secret/key leak finding to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="github",
        signal_type="secret",
        severity="critical",
        category="data",
        title=f"Exposed {key_type} Key",
        detail=f"A {key_type} key was found exposed in {repository}/{file_path}.",
        evidence=_make_evidence_envelope(
            source_service="github_ai_service",
            raw=raw_leak,
            confidence=0.9,
            notes_for_ai=f"Secret leak: {key_type} in public repo",
        ),
    )


# =============================================================================
# AI Risk Signal Converters
# =============================================================================

def ai_tool_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    tool_name: str,
    detection_source: str,
    raw_detection: Dict[str, Any],
    severity: Severity = "low",
) -> Signal:
    """Convert AI tool detection to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="github",
        signal_type="ai_exposure",
        severity=severity,
        category="ai",
        title=f"AI Tool Detected: {tool_name}",
        detail=f"Usage of AI tool {tool_name} was detected via {detection_source}.",
        evidence=_make_evidence_envelope(
            source_service="github_ai_service",
            raw=raw_detection,
            confidence=0.8,
            notes_for_ai=f"AI tool: {tool_name}",
        ),
    )


def ai_agent_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    asset_id: Optional[str],
    agent_name: str,
    agent_type: str,
    detection_source: str,
    raw_detection: Dict[str, Any],
) -> Signal:
    """Convert AI agent detection to a canonical signal."""
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=asset_id,
        source="github",
        signal_type="ai_exposure",
        severity="medium",
        category="ai",
        title=f"AI Agent Detected: {agent_name}",
        detail=f"An AI agent framework ({agent_type}) named {agent_name} was detected via {detection_source}.",
        evidence=_make_evidence_envelope(
            source_service="github_ai_service",
            raw=raw_detection,
            confidence=0.85,
            notes_for_ai=f"Agentic AI: {agent_type}",
        ),
    )


# =============================================================================
# Service Error Signal
# =============================================================================

def service_error_to_signal(
    db: Session,
    org_id: str,
    scan_id: Optional[str],
    service_name: str,
    error_message: str,
    error_type: str,
) -> Signal:
    """
    Create a signal for service errors.
    This allows scans to complete with partial results.
    """
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
    
    return create_canonical_signal(
        db=db,
        org_id=org_id,
        scan_id=scan_id,
        asset_id=None,
        source=service_name.lower(),
        signal_type="config",
        severity="low",
        category="infrastructure",
        title=f"{service_name} Service Unavailable",
        detail=detail,
        evidence=_make_evidence_envelope(
            source_service=f"{service_name.lower()}_service",
            raw={"error": error_message, "error_type": error_type},
            confidence=1.0,
            detection_method="error",
            notes_for_ai=f"Service error: {error_type}",
        ),
    )
