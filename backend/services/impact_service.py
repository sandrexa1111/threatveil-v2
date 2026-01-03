"""
Impact Service - Phase 2 Operational Security Intelligence

Deterministic service for computing decision impact when decisions are resolved.
No LLM involved - all calculations are purely algorithmic.

Confidence scoring rules:
- 1.0: after-scan within 7 days + triggering signal no longer present
- 0.7: after-scan within 7 days, signal presence unknown  
- 0.4: after-scan older than 7 days
- 0.2: no after-scan exists
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models import DecisionImpact, SecurityDecision, Scan, Signal


# =============================================================================
# Confidence Calculation
# =============================================================================

def calculate_confidence(
    decision: SecurityDecision,
    before_scan: Optional[Scan],
    after_scan: Optional[Scan],
    resolved_at: datetime,
    db: Session
) -> Tuple[float, Optional[str]]:
    """
    Calculate confidence score for impact measurement.
    
    Returns:
        Tuple of (confidence_score, notes) where notes explain low confidence.
    
    Rules:
    - 1.0: after-scan within 7 days + at least one triggering signal gone
    - 0.7: after-scan within 7 days, signal status unknown
    - 0.4: after-scan older than 7 days
    - 0.2: no after-scan exists
    """
    if after_scan is None:
        return 0.2, "No scan after resolution - run a new scan to measure impact"
    
    # Calculate days since resolution
    scan_date = after_scan.created_at
    if scan_date.tzinfo is None:
        scan_date = scan_date.replace(tzinfo=timezone.utc)
    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=timezone.utc)
    
    days_since_resolution = (scan_date - resolved_at).days
    
    if days_since_resolution > 7:
        return 0.4, f"After-scan is {days_since_resolution} days old - run a fresh scan for higher confidence"
    
    # Check if triggering signals are gone
    # We need to check if any signals from the before_scan related to this decision
    # are no longer present in the after_scan
    signal_disappeared = _check_signal_disappeared(decision, before_scan, after_scan, db)
    
    if signal_disappeared:
        return 1.0, None
    else:
        return 0.7, "Signal presence unchanged or unknown"


def _check_signal_disappeared(
    decision: SecurityDecision,
    before_scan: Optional[Scan],
    after_scan: Optional[Scan],
    db: Session
) -> bool:
    """
    Check if at least one signal that triggered the decision is no longer present.
    
    This is a heuristic based on comparing signal types/categories between scans.
    """
    if not before_scan or not after_scan:
        return False
    
    # Map action_id to signal characteristics we should look for
    action_to_signal_check = {
        'key-rotation': {'check': 'ai_keys', 'category': None},
        'patch-cves': {'check': 'signals', 'category': 'software', 'severity': 'high'},
        'review-agents': {'check': 'ai_tools', 'category': None},
        'audit-data': {'check': 'signals', 'category': 'data_exposure'},
        'update-tls': {'check': 'signals', 'source': 'tls'},
        'review-network': {'check': 'signals', 'category': 'network'},
        'audit-ai-tools': {'check': 'ai_tools', 'category': None},
    }
    
    check_config = action_to_signal_check.get(decision.action_id)
    if not check_config:
        return False
    
    check_type = check_config.get('check')
    
    if check_type == 'ai_keys':
        # Check if AI key leaks reduced
        before_keys = len(before_scan.scan_ai.ai_keys or []) if before_scan.scan_ai else 0
        after_keys = len(after_scan.scan_ai.ai_keys or []) if after_scan.scan_ai else 0
        return after_keys < before_keys
    
    if check_type == 'ai_tools':
        # Check if AI tools count reduced (agents specifically)
        agent_keywords = ['langchain', 'crewai', 'autogen', 'langgraph', 'agent']
        before_agents = []
        after_agents = []
        
        if before_scan.scan_ai and before_scan.scan_ai.ai_tools:
            before_agents = [t for t in before_scan.scan_ai.ai_tools 
                           if any(kw in t.lower() for kw in agent_keywords)]
        if after_scan.scan_ai and after_scan.scan_ai.ai_tools:
            after_agents = [t for t in after_scan.scan_ai.ai_tools
                          if any(kw in t.lower() for kw in agent_keywords)]
        
        return len(after_agents) < len(before_agents)
    
    if check_type == 'signals':
        # Check if signals matching criteria reduced
        before_signals = before_scan.signals_json or []
        after_signals = after_scan.signals_json or []
        
        def count_matching(signals_list):
            count = 0
            for s in signals_list:
                match = True
                if check_config.get('category') and s.get('category') != check_config['category']:
                    match = False
                if check_config.get('severity') and s.get('severity') != check_config['severity']:
                    match = False
                if check_config.get('source') and s.get('evidence', {}).get('source') != check_config['source']:
                    match = False
                if match:
                    count += 1
            return count
        
        return count_matching(after_signals) < count_matching(before_signals)
    
    return False


# =============================================================================
# Impact Computation
# =============================================================================

def compute_decision_impact(
    db: Session,
    decision: SecurityDecision,
    org_id: str
) -> DecisionImpact:
    """
    Compute impact when a decision is resolved.
    
    This is called when a SecurityDecision transitions to 'resolved' status.
    It creates or updates a DecisionImpact record with:
    - risk_before: from the decision's original scan
    - risk_after: from the most recent scan after resolution
    - delta: risk_after - risk_before (negative = improvement)
    - confidence: based on scan timing and signal presence
    
    Never raises exceptions - stores low confidence with notes if data is insufficient.
    """
    # Get the before scan (the scan that generated this decision)
    before_scan = db.query(Scan).filter(Scan.id == decision.scan_id).first()
    risk_before = before_scan.risk_score if before_scan else (decision.before_score or 0)
    
    # Get the resolved_at timestamp
    resolved_at = decision.resolved_at or datetime.now(timezone.utc)
    
    # Find the most recent scan for this org AFTER the resolution
    after_scan = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at > resolved_at
    ).order_by(Scan.created_at.desc()).first()
    
    # If no scan after resolution, try latest scan (might be same domain)
    if not after_scan and before_scan:
        after_scan = db.query(Scan).filter(
            Scan.domain == before_scan.domain,
            Scan.created_at > decision.created_at,
            Scan.id != before_scan.id
        ).order_by(Scan.created_at.desc()).first()
    
    # Calculate risk values
    risk_after = after_scan.risk_score if after_scan else None
    delta = (risk_after - risk_before) if risk_after is not None else None
    
    # Calculate confidence
    confidence, notes = calculate_confidence(
        decision, before_scan, after_scan, resolved_at, db
    )
    
    # Check if impact already exists
    existing_impact = db.query(DecisionImpact).filter(
        DecisionImpact.decision_id == decision.id
    ).first()
    
    if existing_impact:
        # Update existing
        existing_impact.risk_before = risk_before
        existing_impact.risk_after = risk_after
        existing_impact.delta = delta
        existing_impact.confidence = confidence
        existing_impact.notes = notes
        existing_impact.resolved_scan_id = after_scan.id if after_scan else None
        existing_impact.computed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing_impact)
        return existing_impact
    
    # Create new impact record
    impact = DecisionImpact(
        id=str(uuid.uuid4()),
        org_id=org_id,
        decision_id=decision.id,
        scan_id=before_scan.id if before_scan else None,
        resolved_scan_id=after_scan.id if after_scan else None,
        risk_before=risk_before,
        risk_after=risk_after,
        delta=delta,
        confidence=confidence,
        notes=notes,
        computed_at=datetime.now(timezone.utc)
    )
    
    db.add(impact)
    db.commit()
    db.refresh(impact)
    
    return impact


def get_decision_impact(db: Session, decision_id: str) -> Optional[DecisionImpact]:
    """
    Get the impact record for a decision, if it exists.
    """
    return db.query(DecisionImpact).filter(
        DecisionImpact.decision_id == decision_id
    ).first()
