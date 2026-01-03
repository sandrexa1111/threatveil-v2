"""
Verification Engine - Phase 2.3 Decision Closure

Deterministic verification rules that re-check signals to confirm fixes.

Each verification rule:
1. Checks the relevant signals/evidence for a decision type
2. Returns a result (pass/fail/unknown) with confidence score
3. Captures before/after evidence for proof of fix

Confidence Tiers:
- 1.0 (High): After-scan within 7 days AND triggering signal gone
- 0.7 (Medium): After-scan within 7 days, signal presence unknown
- 0.4 (Low): After-scan older than 7 days
- 0.2 (Very Low): No scan after resolution
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio

from sqlalchemy.orm import Session

from ..models import (
    SecurityDecision, Scan, ScanAI, Signal, 
    DecisionEvidence, DecisionVerificationRun
)
from ..services import http_service, tls_service, dns_service
from ..services.ai.github_ai_service import detect_ai_key_leaks, detect_ai_libraries

logger = logging.getLogger(__name__)


# =============================================================================
# Confidence Calculation
# =============================================================================

def calculate_confidence_tier(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    signal_gone: bool
) -> Tuple[float, str]:
    """
    Calculate confidence score tier based on verification evidence.
    
    Returns: (confidence_score, explanation)
    """
    if not latest_scan:
        return 0.2, "Very Low: No scan after resolution"
    
    if not decision.resolved_at:
        return 0.2, "Very Low: Decision not yet resolved"
    
    # Check if scan is recent (within 7 days of resolution)
    scan_age = datetime.now(timezone.utc) - latest_scan.created_at.replace(tzinfo=timezone.utc)
    is_recent = scan_age <= timedelta(days=7)
    
    if is_recent and signal_gone:
        return 1.0, "High: Recent scan confirms signal is resolved"
    elif is_recent and not signal_gone:
        return 0.7, "Medium: Recent scan but signal status unclear"
    elif signal_gone:
        return 0.4, "Low: Signal resolved but scan is older than 7 days"
    else:
        return 0.4, "Low: Unable to confirm resolution"


# =============================================================================
# Verification Rules by Action ID
# =============================================================================

async def verify_key_rotation(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that leaked API keys have been rotated.
    
    Checks GitHub for the same key patterns that triggered the decision.
    """
    evidence = {"before": {}, "after": {}, "check": "key_rotation"}
    
    # Get original evidence
    scan = decision.scan
    if scan and scan.github_org:
        # Get current key leaks
        try:
            leaks, _ = await detect_ai_key_leaks(scan.github_org)
            evidence["after"]["key_leaks"] = leaks
            
            # Get before evidence from ScanAI
            scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan.id).first()
            if scan_ai:
                evidence["before"]["key_leaks"] = scan_ai.ai_keys or []
            
            original_count = len(evidence["before"].get("key_leaks", []))
            current_count = len(leaks)
            
            if current_count == 0 and original_count > 0:
                confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
                return "pass", confidence, evidence, f"All {original_count} key leak(s) resolved"
            elif current_count < original_count:
                return "pass", 0.7, evidence, f"Reduced from {original_count} to {current_count} leaks"
            elif current_count >= original_count:
                return "fail", 0.9, evidence, f"Key leak(s) still detected: {current_count} found"
            
        except Exception as e:
            logger.warning(f"Error checking key leaks: {e}")
            return "unknown", 0.2, evidence, f"Unable to verify: {str(e)}"
    
    return "unknown", 0.2, evidence, "No GitHub org to verify"


async def verify_hsts_enabled(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that HSTS header is now enabled.
    """
    evidence = {"before": {}, "after": {}, "check": "hsts_enabled"}
    
    scan = decision.scan
    if not scan or not scan.domain:
        return "unknown", 0.2, evidence, "No domain to verify"
    
    try:
        metadata, signals, _ = await http_service.fetch_http_metadata(scan.domain)
        headers = metadata.get("headers", {})
        hsts_present = "strict-transport-security" in headers
        
        evidence["after"]["headers"] = dict(headers)
        evidence["after"]["hsts_present"] = hsts_present
        
        # Get before evidence from signals
        before_signals = [s for s in (scan.signals_json or []) 
                        if 'hsts' in s.get('detail', '').lower() or 'strict-transport' in str(s.get('evidence', {})).lower()]
        evidence["before"]["hsts_signals"] = before_signals
        evidence["before"]["hsts_present"] = len(before_signals) == 0
        
        if hsts_present:
            confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
            return "pass", confidence, evidence, "HSTS header is now enabled"
        else:
            return "fail", 0.9, evidence, "HSTS header still missing"
            
    except Exception as e:
        logger.warning(f"Error checking HSTS: {e}")
        return "unknown", 0.2, evidence, f"Unable to verify: {str(e)}"


async def verify_csp_enabled(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that Content-Security-Policy header is now enabled.
    """
    evidence = {"before": {}, "after": {}, "check": "csp_enabled"}
    
    scan = decision.scan
    if not scan or not scan.domain:
        return "unknown", 0.2, evidence, "No domain to verify"
    
    try:
        metadata, signals, _ = await http_service.fetch_http_metadata(scan.domain)
        headers = metadata.get("headers", {})
        csp_present = "content-security-policy" in headers or "content-security-policy-report-only" in headers
        
        evidence["after"]["headers"] = dict(headers)
        evidence["after"]["csp_present"] = csp_present
        
        if csp_present:
            confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
            return "pass", confidence, evidence, "Content-Security-Policy is now enabled"
        else:
            return "fail", 0.9, evidence, "Content-Security-Policy still missing"
            
    except Exception as e:
        logger.warning(f"Error checking CSP: {e}")
        return "unknown", 0.2, evidence, f"Unable to verify: {str(e)}"


async def verify_tls_fixed(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that TLS certificate issues are resolved (expiry, validity).
    """
    evidence = {"before": {}, "after": {}, "check": "tls_fixed"}
    
    scan = decision.scan
    if not scan or not scan.domain:
        return "unknown", 0.2, evidence, "No domain to verify"
    
    try:
        result = await tls_service.check_tls(scan.domain)
        evidence["after"]["tls"] = result
        
        # Check expiry - cert should be valid for at least 30 days
        days_to_expiry = result.get("days_to_expiry", 0)
        is_valid = result.get("valid", False)
        
        if is_valid and days_to_expiry > 30:
            confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
            return "pass", confidence, evidence, f"TLS certificate valid ({days_to_expiry} days until expiry)"
        elif is_valid and days_to_expiry > 0:
            return "pass", 0.6, evidence, f"TLS valid but expiring soon ({days_to_expiry} days)"
        else:
            return "fail", 0.9, evidence, f"TLS issues remain: {result.get('error', 'certificate invalid')}"
            
    except Exception as e:
        logger.warning(f"Error checking TLS: {e}")
        return "unknown", 0.2, evidence, f"Unable to verify: {str(e)}"


async def verify_cve_patched(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that CVEs are patched by checking if they still appear in latest scan.
    
    Note: This checks Vulners results from the latest scan rather than making a new call.
    """
    evidence = {"before": {}, "after": {}, "check": "cve_patched"}
    
    if not latest_scan:
        return "unknown", 0.2, evidence, "No recent scan to compare"
    
    # Get CVE signals from original and latest scan
    original_cves = [s for s in (decision.scan.signals_json or []) 
                    if s.get('type') == 'cve' or 'CVE-' in s.get('detail', '')]
    latest_cves = [s for s in (latest_scan.signals_json or []) 
                   if s.get('type') == 'cve' or 'CVE-' in s.get('detail', '')]
    
    evidence["before"]["cve_count"] = len(original_cves)
    evidence["before"]["cves"] = [s.get('id') or s.get('detail', '')[:50] for s in original_cves[:5]]
    evidence["after"]["cve_count"] = len(latest_cves)
    evidence["after"]["cves"] = [s.get('id') or s.get('detail', '')[:50] for s in latest_cves[:5]]
    
    original_count = len(original_cves)
    current_count = len(latest_cves)
    
    if current_count == 0 and original_count > 0:
        confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
        return "pass", confidence, evidence, f"All {original_count} CVE(s) resolved"
    elif current_count < original_count:
        reduction = original_count - current_count
        return "pass", 0.7, evidence, f"Reduced CVEs by {reduction} (from {original_count} to {current_count})"
    else:
        return "fail", 0.8, evidence, f"CVEs still present: {current_count} found"


async def verify_ai_agents(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session  
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that exposed AI agent configurations are addressed.
    """
    evidence = {"before": {}, "after": {}, "check": "ai_agents"}
    
    scan = decision.scan
    if not scan or not scan.github_org:
        return "unknown", 0.2, evidence, "No GitHub org to verify"
    
    try:
        libs, detected = await detect_ai_libraries(scan.github_org)
        evidence["after"]["ai_libraries"] = list(detected)
        
        # Get before evidence from ScanAI
        scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan.id).first()
        if scan_ai:
            evidence["before"]["ai_tools"] = scan_ai.ai_tools or []
        
        agent_keywords = ['langchain', 'crewai', 'autogen', 'langgraph', 'agent']
        before_agents = [t for t in evidence["before"].get("ai_tools", []) 
                        if any(kw in t.lower() for kw in agent_keywords)]
        after_agents = [t for t in detected 
                       if any(kw in t.lower() for kw in agent_keywords)]
        
        evidence["before"]["agents"] = before_agents
        evidence["after"]["agents"] = after_agents
        
        if len(after_agents) < len(before_agents):
            confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
            return "pass", confidence, evidence, f"Reduced exposed agents from {len(before_agents)} to {len(after_agents)}"
        elif len(after_agents) == 0:
            return "pass", 0.9, evidence, "No exposed agent configurations detected"
        else:
            return "fail", 0.7, evidence, f"Agent configurations still exposed: {len(after_agents)}"
            
    except Exception as e:
        logger.warning(f"Error checking AI agents: {e}")
        return "unknown", 0.2, evidence, f"Unable to verify: {str(e)}"


async def verify_data_exposure(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that data exposure issues are addressed.
    """
    evidence = {"before": {}, "after": {}, "check": "data_exposure"}
    
    if not latest_scan:
        return "unknown", 0.2, evidence, "No recent scan to compare"
    
    # Check data exposure signals
    before_exposure = [s for s in (decision.scan.signals_json or []) 
                      if s.get('category') == 'data_exposure']
    after_exposure = [s for s in (latest_scan.signals_json or []) 
                     if s.get('category') == 'data_exposure']
    
    evidence["before"]["data_exposure_count"] = len(before_exposure)
    evidence["after"]["data_exposure_count"] = len(after_exposure)
    
    if len(after_exposure) < len(before_exposure):
        confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
        return "pass", confidence, evidence, f"Data exposure reduced from {len(before_exposure)} to {len(after_exposure)}"
    elif len(after_exposure) == 0:
        return "pass", 0.9, evidence, "No data exposure issues detected"
    else:
        return "fail", 0.7, evidence, f"Data exposure issues remain: {len(after_exposure)}"


async def verify_network_issues(
    decision: SecurityDecision,
    latest_scan: Optional[Scan],
    db: Session
) -> Tuple[str, float, Dict[str, Any], str]:
    """
    Verify that network configuration issues are resolved.
    """
    evidence = {"before": {}, "after": {}, "check": "network_issues"}
    
    if not latest_scan:
        return "unknown", 0.2, evidence, "No recent scan to compare"
    
    # Check network signals (non-low severity)
    before_network = [s for s in (decision.scan.signals_json or []) 
                     if s.get('category') == 'network' and s.get('severity') != 'low']
    after_network = [s for s in (latest_scan.signals_json or [])
                    if s.get('category') == 'network' and s.get('severity') != 'low']
    
    evidence["before"]["network_issues"] = len(before_network)
    evidence["after"]["network_issues"] = len(after_network)
    
    if len(after_network) < len(before_network):
        confidence, reason = calculate_confidence_tier(decision, latest_scan, True)
        return "pass", confidence, evidence, f"Network issues reduced from {len(before_network)} to {len(after_network)}"
    elif len(after_network) == 0:
        return "pass", 0.9, evidence, "No network issues detected"
    else:
        return "fail", 0.7, evidence, f"Network issues remain: {len(after_network)}"


# Action ID to verification function mapping
VERIFICATION_RULES: Dict[str, Callable] = {
    'key-rotation': verify_key_rotation,
    'patch-cves': verify_cve_patched,
    'enable-hsts': verify_hsts_enabled,
    'enable-csp': verify_csp_enabled,
    'update-tls': verify_tls_fixed,
    'review-agents': verify_ai_agents,
    'audit-data': verify_data_exposure,
    'review-network': verify_network_issues,
    # Aliases for common action IDs
    'rotate-keys': verify_key_rotation,
    'fix-headers': verify_hsts_enabled,
}


# =============================================================================
# Main Verification Functions
# =============================================================================

async def run_verification(
    db: Session,
    decision: SecurityDecision
) -> DecisionVerificationRun:
    """
    Run verification for a decision and create a verification run record.
    
    Args:
        db: Database session
        decision: The decision to verify
        
    Returns:
        DecisionVerificationRun with result, confidence, and evidence
    """
    # Create verification run record
    run = DecisionVerificationRun(
        decision_id=decision.id,
        started_at=datetime.now(timezone.utc),
        result="unknown",
        confidence=0.2,
        evidence={}
    )
    db.add(run)
    
    # Get latest scan for comparison
    latest_scan = db.query(Scan).filter(
        Scan.domain == decision.scan.domain,
        Scan.created_at > decision.resolved_at if decision.resolved_at else Scan.created_at > decision.created_at
    ).order_by(Scan.created_at.desc()).first()
    
    # Get verification rule for this action
    verify_func = VERIFICATION_RULES.get(decision.action_id)
    
    if not verify_func:
        # No specific rule - use generic signal comparison
        run.result = "unknown"
        run.confidence = 0.4
        run.notes = f"No verification rule for action: {decision.action_id}"
        run.evidence = {"check": "none", "action_id": decision.action_id}
    else:
        try:
            result, confidence, evidence, notes = await verify_func(decision, latest_scan, db)
            run.result = result
            run.confidence = confidence
            run.evidence = evidence
            run.notes = notes
        except Exception as e:
            logger.error(f"Verification failed for decision {decision.id}: {e}")
            run.result = "unknown"
            run.confidence = 0.2
            run.notes = f"Verification error: {str(e)}"
            run.evidence = {"error": str(e)}
    
    run.completed_at = datetime.now(timezone.utc)
    
    # Store evidence records
    if run.evidence.get("before"):
        before_evidence = DecisionEvidence(
            decision_id=decision.id,
            scan_id=decision.scan_id,
            type="before",
            payload=run.evidence.get("before", {})
        )
        db.add(before_evidence)
    
    if run.evidence.get("after"):
        after_evidence = DecisionEvidence(
            decision_id=decision.id,
            scan_id=latest_scan.id if latest_scan else None,
            type="after",
            payload=run.evidence.get("after", {})
        )
        db.add(after_evidence)
    
    # Update decision status based on result
    if run.result == "pass":
        decision.status = "verified"
        decision.verified_at = datetime.now(timezone.utc)
        decision.verification_status = "pass"
        decision.confidence_score = run.confidence
        decision.confidence_reason = run.notes
        if latest_scan:
            decision.verification_scan_id = latest_scan.id
    elif run.result == "fail":
        decision.verification_status = "fail"
        decision.verification_notes = run.notes
    else:
        decision.verification_status = "unknown"
        decision.verification_notes = run.notes
    
    decision.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(run)
    
    logger.info(f"Verification complete for decision {decision.id}: {run.result} ({run.confidence:.1f})")
    
    return run


def get_latest_verification_run(
    db: Session,
    decision_id: str
) -> Optional[DecisionVerificationRun]:
    """Get the most recent verification run for a decision."""
    return db.query(DecisionVerificationRun).filter(
        DecisionVerificationRun.decision_id == decision_id
    ).order_by(DecisionVerificationRun.created_at.desc()).first()


def get_verification_evidence(
    db: Session,
    decision_id: str
) -> Dict[str, Any]:
    """Get before/after evidence for a decision."""
    evidence_records = db.query(DecisionEvidence).filter(
        DecisionEvidence.decision_id == decision_id
    ).order_by(DecisionEvidence.created_at.desc()).all()
    
    result = {"before": None, "after": None}
    for record in evidence_records:
        if record.type == "before" and result["before"] is None:
            result["before"] = record.payload
        elif record.type == "after" and result["after"] is None:
            result["after"] = record.payload
    
    return result
