"""
Verification Routes - Phase 2.3 Decision Closure

Provides endpoints for verifying security decisions:
- POST /api/v1/decisions/{id}/verify - Trigger verification
- GET /api/v1/decisions/{id}/verification - Get verification details
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import SecurityDecision, DecisionVerificationRun, DecisionEvidence
from ..schemas import (
    VerificationRunResponse, 
    VerificationDetailResponse,
    DecisionEvidenceRead
)
from ..services.verification_engine import (
    run_verification, 
    get_latest_verification_run,
    get_verification_evidence
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/decisions", tags=["verification"])


# =============================================================================
# Verification Endpoints
# =============================================================================

@router.post("/{decision_id}/verify", response_model=VerificationRunResponse)
async def verify_decision(
    decision_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger verification for a resolved decision.
    
    Runs deterministic checks to confirm the fix was applied.
    Updates decision status to 'verified' if checks pass.
    
    Prerequisites:
    - Decision must exist
    - Decision should be in 'resolved' status (will still run for other statuses)
    
    Returns:
        VerificationRunResponse with result, confidence, and notes
    """
    # Get decision
    decision = db.query(SecurityDecision).filter(
        SecurityDecision.id == decision_id
    ).first()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Warn if not resolved
    if decision.status not in ['resolved', 'verified']:
        logger.warning(f"Running verification on decision {decision_id} with status {decision.status}")
    
    # Run verification
    try:
        run = await run_verification(db, decision)
        
        return VerificationRunResponse(
            id=run.id,
            decision_id=run.decision_id,
            result=run.result,
            confidence=run.confidence,
            notes=run.notes,
            evidence=run.evidence,
            started_at=run.started_at,
            completed_at=run.completed_at
        )
    except Exception as e:
        logger.error(f"Verification failed for decision {decision_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/{decision_id}/verification", response_model=VerificationDetailResponse)
async def get_verification_details(
    decision_id: str,
    db: Session = Depends(get_db)
):
    """
    Get verification details for a decision.
    
    Returns:
        - Latest verification run (if any)
        - Before/after evidence
        - Confidence explanation
        - Total run count
    """
    # Verify decision exists
    decision = db.query(SecurityDecision).filter(
        SecurityDecision.id == decision_id
    ).first()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Get latest verification run
    latest_run = get_latest_verification_run(db, decision_id)
    
    # Get evidence
    evidence = get_verification_evidence(db, decision_id)
    
    # Get total runs
    total_runs = db.query(DecisionVerificationRun).filter(
        DecisionVerificationRun.decision_id == decision_id
    ).count()
    
    # Build confidence explanation
    if latest_run:
        confidence_explanation = f"{latest_run.notes or ''} (Confidence: {latest_run.confidence:.0%})"
    elif decision.verification_status:
        confidence_explanation = decision.verification_notes or f"Status: {decision.verification_status}"
    else:
        confidence_explanation = "No verification run yet"
    
    return VerificationDetailResponse(
        decision_id=decision_id,
        latest_run=VerificationRunResponse(
            id=latest_run.id,
            decision_id=latest_run.decision_id,
            result=latest_run.result,
            confidence=latest_run.confidence,
            notes=latest_run.notes,
            evidence=latest_run.evidence,
            started_at=latest_run.started_at,
            completed_at=latest_run.completed_at
        ) if latest_run else None,
        evidence_before=evidence.get("before") or {},
        evidence_after=evidence.get("after"),
        confidence_explanation=confidence_explanation,
        all_runs_count=total_runs
    )


@router.get("/{decision_id}/evidence")
async def list_decision_evidence(
    decision_id: str,
    db: Session = Depends(get_db)
):
    """
    List all evidence records for a decision.
    """
    decision = db.query(SecurityDecision).filter(
        SecurityDecision.id == decision_id
    ).first()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    evidence_records = db.query(DecisionEvidence).filter(
        DecisionEvidence.decision_id == decision_id
    ).order_by(DecisionEvidence.created_at.desc()).all()
    
    return {
        "decision_id": decision_id,
        "evidence": [
            DecisionEvidenceRead(
                id=e.id,
                decision_id=e.decision_id,
                scan_id=e.scan_id,
                type=e.type,
                payload=e.payload,
                created_at=e.created_at
            ) for e in evidence_records
        ]
    }
