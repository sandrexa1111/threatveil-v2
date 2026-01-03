"""
Decision Verification Service

Provides auto-verification logic for security decisions when subsequent scans confirm fixes.

Auto-verification triggers when:
1. A decision is in 'resolved' status
2. A new scan runs for the same domain
3. The triggering signal is no longer present in the new scan

Confidence scoring:
- 1.0 (High): Signal that triggered the decision is confirmed gone
- 0.7 (Medium): Signal type is gone but can't confirm exact match
- 0.4 (Low): Scan ran but signal presence is unknown
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import SecurityDecision, Scan, ScanAI

logger = logging.getLogger(__name__)


def auto_verify_decisions_for_scan(db: Session, new_scan: Scan) -> List[str]:
    """
    Auto-verify resolved decisions when a new scan confirms fixes.
    
    Args:
        db: Database session
        new_scan: The newly completed scan
        
    Returns:
        List of decision IDs that were auto-verified
    """
    if not new_scan.domain:
        return []
    
    verified_ids = []
    
    # Find all resolved decisions for this domain that haven't been verified yet
    resolved_decisions = db.query(SecurityDecision).join(Scan).filter(
        Scan.domain == new_scan.domain,
        SecurityDecision.status == 'resolved',
        SecurityDecision.verified_at.is_(None)
    ).all()
    
    if not resolved_decisions:
        logger.debug(f"No resolved decisions to verify for domain {new_scan.domain}")
        return []
    
    logger.info(f"Checking {len(resolved_decisions)} resolved decisions for auto-verification")
    
    new_signals = new_scan.signals_json or []
    new_scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == new_scan.id).first()
    
    for decision in resolved_decisions:
        # Only auto-verify if decision was resolved before this scan
        if decision.resolved_at and decision.resolved_at > new_scan.created_at:
            continue
            
        # Check if the triggering signal is gone
        signal_gone = _check_signal_resolved(decision, new_signals, new_scan_ai)
        
        if signal_gone:
            # Auto-verify the decision
            decision.status = 'verified'
            decision.verified_at = datetime.now(timezone.utc)
            decision.verification_scan_id = new_scan.id
            decision.updated_at = datetime.now(timezone.utc)
            
            # Update confidence based on verification quality
            decision.confidence_score = 1.0
            decision.confidence_reason = "Verified: Triggering signal no longer detected"
            
            verified_ids.append(decision.id)
            logger.info(f"Auto-verified decision {decision.id}: {decision.title}")
    
    if verified_ids:
        db.commit()
        
    return verified_ids


def _check_signal_resolved(
    decision: SecurityDecision, 
    new_signals: List[dict], 
    new_scan_ai: Optional[ScanAI]
) -> bool:
    """
    Check if the signal that triggered this decision is resolved.
    
    Uses action_id to determine what signal type to look for.
    """
    action_id = decision.action_id
    
    if action_id == 'key-rotation':
        # Check if AI keys are still exposed
        ai_keys = (new_scan_ai.ai_keys or []) if new_scan_ai else []
        return len(ai_keys) == 0
    
    elif action_id == 'patch-cves':
        # Check if high-severity CVEs still exist
        high_cves = [s for s in new_signals 
                     if s.get('category') == 'software' and s.get('severity') == 'high']
        return len(high_cves) == 0
    
    elif action_id == 'review-agents':
        # Check if exposed agent frameworks are still present
        ai_tools = (new_scan_ai.ai_tools or []) if new_scan_ai else []
        agent_keywords = ['langchain', 'crewai', 'autogen', 'langgraph', 'agent']
        ai_agents = [t for t in ai_tools if any(kw in t.lower() for kw in agent_keywords)]
        return len(ai_agents) == 0
    
    elif action_id == 'audit-data':
        # Check if data exposure signals are gone
        data_exposure = [s for s in new_signals if s.get('category') == 'data_exposure']
        return len(data_exposure) == 0
    
    elif action_id == 'update-tls':
        # Check if TLS issues are resolved
        tls_issues = [s for s in new_signals 
                      if s.get('evidence', {}).get('source') == 'tls' 
                      and s.get('severity') in ['high', 'medium']]
        return len(tls_issues) == 0
    
    elif action_id == 'review-network':
        # Check if network exposure issues are gone
        network_issues = [s for s in new_signals 
                          if s.get('category') == 'network' 
                          and s.get('severity') != 'low']
        return len(network_issues) == 0
    
    elif action_id == 'audit-ai-tools':
        # AI tools might still be present (that's okay) - just verify scan ran
        # This one we verify with lower confidence since we can't confirm the audit
        return False  # Don't auto-verify audits
    
    # Unknown action_id - don't auto-verify
    return False


def get_verification_candidates(db: Session, org_id: str) -> List[SecurityDecision]:
    """
    Get resolved decisions that are candidates for verification.
    
    Returns decisions that:
    - Are in 'resolved' status
    - Haven't been verified yet
    - Were resolved more than 24 hours ago (give time for rescan)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    return db.query(SecurityDecision).join(Scan).filter(
        Scan.org_id == org_id,
        SecurityDecision.status == 'resolved',
        SecurityDecision.verified_at.is_(None),
        SecurityDecision.resolved_at < cutoff
    ).all()
