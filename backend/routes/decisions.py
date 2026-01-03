"""
Decision routes for the Weekly Security Loop feature.

Provides endpoints to:
- Generate decisions for a scan (deterministic, no LLM)
- List decisions for a scan
- Update decision status (pending → in_progress → resolved)
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Scan, ScanAI, SecurityDecision, DecisionImpact
from ..services.impact_service import compute_decision_impact, get_decision_impact


router = APIRouter(prefix="/api/v1", tags=["decisions"])


# =============================================================================
# Schemas
# =============================================================================

class DecisionResponse(BaseModel):
    id: str
    scan_id: str
    action_id: str
    title: str
    recommended_fix: str
    effort_estimate: str
    estimated_risk_reduction: int
    priority: int
    status: str
    before_score: Optional[int] = None
    after_score: Optional[int] = None
    business_impact: Optional[str] = None
    confidence_score: float = 0.8
    confidence_reason: Optional[str] = None
    verification_scan_id: Optional[str] = None
    created_at: str
    updated_at: str
    accepted_at: Optional[str] = None
    resolved_at: Optional[str] = None
    verified_at: Optional[str] = None

    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    decisions: List[DecisionResponse]
    pending_count: int
    accepted_count: int
    in_progress_count: int
    resolved_count: int
    verified_count: int
    total_risk_reduction: int


class UpdateStatusRequest(BaseModel):
    status: str  # 'pending' | 'accepted' | 'in_progress' | 'resolved' | 'verified'


class UpdateStatusResponse(BaseModel):
    decision: DecisionResponse
    risk_delta: Optional[int] = None  # before_score - after_score


class DecisionImpactResponse(BaseModel):
    """Response for GET /decisions/{decision_id}/impact"""
    decision_id: str
    risk_before: int
    risk_after: Optional[int] = None
    delta: Optional[int] = None
    confidence: float
    computed_at: str
    notes: Optional[str] = None


# =============================================================================
# Decision Generation Logic (Deterministic - No LLM)
# =============================================================================

# Priority mapping mirrors frontend SecurityDecisionsCard.tsx
DECISION_TEMPLATES = {
    'key-rotation': {
        'title': 'Rotate Exposed Credentials',
        'recommended_fix': 'Immediately rotate all exposed API keys and secrets. Revoke old credentials and audit access logs for unauthorized usage.',
        'effort_estimate': '1 hour',
        'estimated_risk_reduction': 25,
        'priority': 1,
    },
    'patch-cves': {
        'title': 'Patch Critical Vulnerabilities',
        'recommended_fix': 'Apply vendor patches for detected CVEs. Prioritize high-severity vulnerabilities with known exploits.',
        'effort_estimate': '2-4 hours',
        'estimated_risk_reduction': 20,
        'priority': 2,
    },
    'review-agents': {
        'title': 'Review Agent Access Controls',
        'recommended_fix': 'Audit exposed agentic frameworks. Restrict access permissions and ensure agents operate with minimal privileges.',
        'effort_estimate': '2 hours',
        'estimated_risk_reduction': 15,
        'priority': 3,
    },
    'audit-data': {
        'title': 'Audit Data Access Policies',
        'recommended_fix': 'Review data exposure signals. Implement proper access controls and audit data handling procedures.',
        'effort_estimate': '1-2 hours',
        'estimated_risk_reduction': 15,
        'priority': 4,
    },
    'update-tls': {
        'title': 'Update Certificate Configuration',
        'recommended_fix': 'Update TLS certificates and configuration. Ensure modern cipher suites and proper certificate chain.',
        'effort_estimate': '30 mins',
        'estimated_risk_reduction': 10,
        'priority': 5,
    },
    'review-network': {
        'title': 'Review Network Exposure',
        'recommended_fix': 'Audit external network exposure. Close unnecessary ports and restrict access to internal services.',
        'effort_estimate': '1 hour',
        'estimated_risk_reduction': 10,
        'priority': 6,
    },
    'audit-ai-tools': {
        'title': 'Audit AI Tool Usage',
        'recommended_fix': 'Review detected AI tools for data handling compliance. Maintain inventory of approved tools.',
        'effort_estimate': '1 hour',
        'estimated_risk_reduction': 5,
        'priority': 7,
    },
}


def generate_decisions_for_scan(scan: Scan, scan_ai: Optional[ScanAI]) -> List[dict]:
    """
    Deterministically generate security decisions based on scan findings.
    
    This mirrors the frontend generateActions() logic exactly to ensure
    consistency between what the UI shows and what gets persisted.
    """
    decisions = []
    signals = scan.signals_json or []
    
    # Priority 1: Key leaks
    ai_keys = (scan_ai.ai_keys or []) if scan_ai else []
    if len(ai_keys) > 0:
        decisions.append({
            'action_id': 'key-rotation',
            **DECISION_TEMPLATES['key-rotation'],
        })
    
    # Priority 2: High-severity CVEs
    high_cves = [s for s in signals if s.get('category') == 'software' and s.get('severity') == 'high']
    if len(high_cves) > 0:
        decisions.append({
            'action_id': 'patch-cves',
            **DECISION_TEMPLATES['patch-cves'],
        })
    
    # Priority 3: Agent frameworks
    ai_tools = (scan_ai.ai_tools or []) if scan_ai else []
    agent_keywords = ['langchain', 'crewai', 'autogen', 'langgraph', 'agent']
    ai_agents = [t for t in ai_tools if any(kw in t.lower() for kw in agent_keywords)]
    if len(ai_agents) > 0:
        decisions.append({
            'action_id': 'review-agents',
            **DECISION_TEMPLATES['review-agents'],
        })
    
    # Priority 4: Data exposure
    data_exposure = [s for s in signals if s.get('category') == 'data_exposure']
    if len(data_exposure) > 0:
        decisions.append({
            'action_id': 'audit-data',
            **DECISION_TEMPLATES['audit-data'],
        })
    
    # Priority 5: TLS issues
    tls_issues = [s for s in signals 
                  if s.get('evidence', {}).get('source') == 'tls' 
                  and s.get('severity') in ['high', 'medium']]
    if len(tls_issues) > 0:
        decisions.append({
            'action_id': 'update-tls',
            **DECISION_TEMPLATES['update-tls'],
        })
    
    # Priority 6: Network exposure (only if we have < 3 decisions)
    network_issues = [s for s in signals 
                      if s.get('category') == 'network' 
                      and s.get('severity') != 'low']
    if len(network_issues) > 0 and len(decisions) < 3:
        decisions.append({
            'action_id': 'review-network',
            **DECISION_TEMPLATES['review-network'],
        })
    
    # Priority 7: AI tools (only if we have < 3 decisions)
    if len(ai_tools) > 0 and len(decisions) < 3:
        decisions.append({
            'action_id': 'audit-ai-tools',
            **DECISION_TEMPLATES['audit-ai-tools'],
        })
    
    # Return top 3
    return sorted(decisions, key=lambda d: d['priority'])[:3]


# =============================================================================
# Routes
# =============================================================================

@router.post("/scans/{scan_id}/decisions", response_model=DecisionListResponse)
async def generate_decisions(scan_id: str, db: Session = Depends(get_db)):
    """
    Generate security decisions for a scan.
    
    Decisions are generated deterministically based on scan findings.
    If decisions already exist, returns existing decisions.
    """
    # Check scan exists
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Check if decisions already exist
    existing = db.query(SecurityDecision).filter(SecurityDecision.scan_id == scan_id).all()
    if existing:
        # Return existing decisions
        return _build_decision_list_response(existing)
    
    # Get AI data if available
    scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan_id).first()
    
    # Generate decisions
    decision_dicts = generate_decisions_for_scan(scan, scan_ai)
    
    # Persist decisions
    decisions = []
    for d in decision_dicts:
        decision = SecurityDecision(
            id=str(uuid.uuid4()),
            scan_id=scan_id,
            action_id=d['action_id'],
            title=d['title'],
            recommended_fix=d['recommended_fix'],
            effort_estimate=d['effort_estimate'],
            estimated_risk_reduction=d['estimated_risk_reduction'],
            priority=d['priority'],
            status='pending',
            before_score=scan.risk_score,  # Store current risk score
        )
        db.add(decision)
        decisions.append(decision)
    
    db.commit()
    
    # Refresh to get updated timestamps
    for d in decisions:
        db.refresh(d)
    
    return _build_decision_list_response(decisions)


@router.get("/scans/{scan_id}/decisions", response_model=DecisionListResponse)
async def get_decisions(scan_id: str, db: Session = Depends(get_db)):
    """
    Get all decisions for a scan.
    """
    # Check scan exists
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    decisions = db.query(SecurityDecision).filter(
        SecurityDecision.scan_id == scan_id
    ).order_by(SecurityDecision.priority).all()
    
    return _build_decision_list_response(decisions)


@router.patch("/decisions/{decision_id}", response_model=UpdateStatusResponse)
async def update_decision_status(
    decision_id: str, 
    request: UpdateStatusRequest, 
    db: Session = Depends(get_db)
):
    """
    Update decision status.
    
    Valid transitions:
    - pending → accepted | in_progress | resolved
    - accepted → in_progress | resolved
    - in_progress → resolved | accepted (can step back)
    - resolved → verified | in_progress (can step back)
    - verified → (terminal state, can go back to resolved)
    
    When status changes to 'resolved':
    - Sets resolved_at timestamp
    - Fetches latest scan for the domain to calculate risk delta
    - Stores after_score
    
    When status changes to 'verified':
    - Sets verified_at timestamp
    - Must already be in 'resolved' state
    """
    valid_statuses = ['pending', 'accepted', 'in_progress', 'resolved', 'verified']
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    decision = db.query(SecurityDecision).filter(SecurityDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Validate transition for verified
    if request.status == 'verified' and decision.status != 'resolved':
        raise HTTPException(
            status_code=400, 
            detail="Decision must be resolved before it can be verified"
        )
    
    # Update status
    old_status = decision.status
    decision.status = request.status
    decision.updated_at = datetime.now(timezone.utc)
    
    risk_delta = None
    
    # Handle accepted status
    if request.status == 'accepted' and old_status not in ('accepted', 'in_progress', 'resolved', 'verified'):
        decision.accepted_at = datetime.now(timezone.utc)
    
    # If marking as resolved, calculate risk delta and compute impact
    if request.status == 'resolved' and old_status != 'resolved':
        decision.resolved_at = datetime.now(timezone.utc)
        
        # Get the scan to find the domain and org_id
        scan = db.query(Scan).filter(Scan.id == decision.scan_id).first()
        if scan:
            # Get latest scan for this domain to compare risk
            latest_scan = db.query(Scan).filter(
                Scan.domain == scan.domain
            ).order_by(Scan.created_at.desc()).first()
            
            if latest_scan:
                decision.after_score = latest_scan.risk_score
                if decision.before_score is not None:
                    risk_delta = decision.before_score - decision.after_score
            
            # Compute and store impact (Phase 2)
            # This never fails - stores low confidence if data insufficient
            try:
                org_id = scan.org_id or scan.company_id
                if org_id:
                    compute_decision_impact(db, decision, org_id)
            except Exception:
                # Never block the request if impact computation fails
                pass
    
    # Handle verified status
    if request.status == 'verified' and old_status == 'resolved':
        decision.verified_at = datetime.now(timezone.utc)
        
        # Link to the verification scan (latest scan after resolution)
        scan = db.query(Scan).filter(Scan.id == decision.scan_id).first()
        if scan and decision.resolved_at:
            verification_scan = db.query(Scan).filter(
                Scan.domain == scan.domain,
                Scan.created_at > decision.resolved_at
            ).order_by(Scan.created_at.desc()).first()
            
            if verification_scan:
                decision.verification_scan_id = verification_scan.id
    
    # If moving back from resolved, clear resolved_at and delete impact
    if request.status not in ('resolved', 'verified') and old_status in ('resolved', 'verified'):
        decision.resolved_at = None
        decision.after_score = None
        decision.verified_at = None
        decision.verification_scan_id = None
        # Also remove impact record
        db.query(DecisionImpact).filter(DecisionImpact.decision_id == decision_id).delete()
    
    db.commit()
    db.refresh(decision)
    
    return UpdateStatusResponse(
        decision=_decision_to_response(decision),
        risk_delta=risk_delta
    )


@router.get("/decisions/{decision_id}/impact", response_model=DecisionImpactResponse)
async def get_impact(decision_id: str, db: Session = Depends(get_db)):
    """
    Get the computed impact for a resolved decision.
    
    Returns 404 if:
    - Decision doesn't exist
    - Decision is not resolved
    - Impact hasn't been computed yet
    """
    # Check decision exists
    decision = db.query(SecurityDecision).filter(SecurityDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Get impact
    impact = get_decision_impact(db, decision_id)
    if not impact:
        raise HTTPException(
            status_code=404, 
            detail="Impact not computed. Resolve the decision first."
        )
    
    return DecisionImpactResponse(
        decision_id=impact.decision_id,
        risk_before=impact.risk_before,
        risk_after=impact.risk_after,
        delta=impact.delta,
        confidence=impact.confidence,
        computed_at=impact.computed_at.isoformat() if impact.computed_at else "",
        notes=impact.notes
    )


# =============================================================================
# Helpers
# =============================================================================

def _decision_to_response(decision: SecurityDecision) -> DecisionResponse:
    return DecisionResponse(
        id=decision.id,
        scan_id=decision.scan_id,
        action_id=decision.action_id,
        title=decision.title,
        recommended_fix=decision.recommended_fix,
        effort_estimate=decision.effort_estimate,
        estimated_risk_reduction=decision.estimated_risk_reduction,
        priority=decision.priority,
        status=decision.status,
        before_score=decision.before_score,
        after_score=decision.after_score,
        business_impact=decision.business_impact,
        confidence_score=decision.confidence_score,
        confidence_reason=decision.confidence_reason,
        verification_scan_id=decision.verification_scan_id,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
        updated_at=decision.updated_at.isoformat() if decision.updated_at else "",
        accepted_at=decision.accepted_at.isoformat() if decision.accepted_at else None,
        resolved_at=decision.resolved_at.isoformat() if decision.resolved_at else None,
        verified_at=decision.verified_at.isoformat() if decision.verified_at else None,
    )


def _build_decision_list_response(decisions: List[SecurityDecision]) -> DecisionListResponse:
    pending = [d for d in decisions if d.status == 'pending']
    accepted = [d for d in decisions if d.status == 'accepted']
    in_progress = [d for d in decisions if d.status == 'in_progress']
    resolved = [d for d in decisions if d.status == 'resolved']
    verified = [d for d in decisions if d.status == 'verified']
    
    # Sum estimated risk reduction for unresolved decisions (pending + accepted + in_progress)
    unresolved = pending + accepted + in_progress
    total_reduction = sum(d.estimated_risk_reduction for d in unresolved)
    
    return DecisionListResponse(
        decisions=[_decision_to_response(d) for d in decisions],
        pending_count=len(pending),
        accepted_count=len(accepted),
        in_progress_count=len(in_progress),
        resolved_count=len(resolved),
        verified_count=len(verified),
        total_risk_reduction=total_reduction,
    )

