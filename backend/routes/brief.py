"""
Daily Brief Routes (Phase 2 Placeholder)

API endpoints for daily security brief:
- GET /api/v1/brief/{org_id} - Get daily security brief for organization
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Organization, Scan, Signal, ScanAI
from ..schemas import DailyBriefResponse, SignalRead, AssetSummary

router = APIRouter(prefix="/api/v1/brief", tags=["brief"])


def get_current_org_id(org_id: str, db: Session) -> str:
    """Validate and return the org_id."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_id


def signal_to_read_simple(signal: Signal) -> SignalRead:
    """Convert a Signal model to SignalRead schema (simplified)."""
    return SignalRead(
        id=signal.id,
        org_id=signal.org_id,
        scan_id=signal.scan_id,
        asset_id=signal.asset_id,
        source=signal.source,
        type=signal.type,
        severity=signal.severity,
        category=signal.category,
        title=signal.title,
        detail=signal.detail,
        evidence=signal.evidence,
        created_at=signal.created_at,
        asset=None,
    )


@router.get("/{org_id}", response_model=DailyBriefResponse)
async def get_daily_brief(
    org_id: str,
    db: Session = Depends(get_db),
):
    """
    Get daily security brief for an organization.
    
    This is a Phase 2 placeholder that returns real top signals
    and placeholder data for upcoming features.
    """
    # Validate org access
    get_current_org_id(org_id, db)
    
    # Get top 3 high-severity signals
    top_signals = db.query(Signal).filter(
        Signal.org_id == org_id,
        Signal.severity.in_(["critical", "high"])
    ).order_by(desc(Signal.created_at)).limit(3).all()
    
    top_signal_reads = [signal_to_read_simple(s) for s in top_signals]
    
    # Get latest scan for AI exposure
    last_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    ai_exposure = "low"
    last_scan_id = None
    
    if last_scan:
        last_scan_id = last_scan.id
        # Get AI exposure from ScanAI if available
        if last_scan.scan_ai:
            ai_exposure = last_scan.scan_ai.ai_exposure_level
    
    # Return brief with placeholder actions
    return DailyBriefResponse(
        top_signals=top_signal_reads,
        top_actions=[
            "Review critical signals and prioritize remediation",
            "Update security headers on exposed domains",
            "Audit AI API keys and rotate if necessary",
        ],
        risk_delta=0.0,  # Placeholder - would compare to previous brief
        ai_exposure=ai_exposure,
        attack_path_summary="Attack path analysis coming in Phase 2",
        last_scan_id=last_scan_id,
    )
