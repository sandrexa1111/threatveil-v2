"""
Organization Routes

API endpoints for organization-level data:
- GET /api/v1/org/{org_id}/signals - Query signals with filters
- GET /api/v1/org/{org_id}/summary - Organization summary/aggregations
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Asset, Organization, Scan, Signal, ScanAI
from ..schemas import (
    EnhancedOrgSummary,
    OrgSummary,
    Severity,
    SignalListResponse,
    SignalRead,
    AssetSummary,
)

router = APIRouter(prefix="/api/v1/org", tags=["organization"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_current_org_id(org_id: str, db: Session) -> str:
    """
    Validate and return the org_id.
    In a real implementation, this would verify the authenticated user
    has access to this organization.
    
    For Phase 1, we just verify the org exists.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_id


def signal_to_read(signal: Signal, db: Session) -> SignalRead:
    """Convert a Signal model to SignalRead schema."""
    asset_summary = None
    if signal.asset_id:
        asset = db.query(Asset).filter(Asset.id == signal.asset_id).first()
        if asset:
            asset_summary = AssetSummary(
                id=asset.id,
                type=asset.type,
                name=asset.name,
            )
    
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
        asset=asset_summary,
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{org_id}/signals", response_model=SignalListResponse)
async def get_org_signals(
    org_id: str,
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    source: Optional[str] = Query(None, description="Filter by source"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get signals for an organization with optional filters.
    
    Returns paginated list of canonical signals with asset info.
    """
    # Validate org access
    get_current_org_id(org_id, db)
    
    # Build query
    query = db.query(Signal).filter(Signal.org_id == org_id)
    
    # Apply filters
    if severity:
        query = query.filter(Signal.severity == severity)
    if category:
        query = query.filter(Signal.category == category)
    if asset_id:
        query = query.filter(Signal.asset_id == asset_id)
    if source:
        query = query.filter(Signal.source == source)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    signals = query.order_by(desc(Signal.created_at)).offset(offset).limit(page_size).all()
    
    # Convert to response schema
    signal_reads = [signal_to_read(s, db) for s in signals]
    
    return SignalListResponse(
        signals=signal_reads,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(signals)) < total,
    )


@router.get("/{org_id}/summary", response_model=EnhancedOrgSummary)
async def get_org_summary(
    org_id: str,
    db: Session = Depends(get_db),
):
    """
    Get enhanced organization summary with aggregated signal counts.
    
    Returns:
    - Total signals
    - Signals by severity
    - Signals by category
    - Total assets
    - Total scans
    - Risk trend (last 7 scans sparkline)
    - AI exposure level
    - Top 3 recurring risks
    - Last scan timestamp
    - Top 5 high-severity signals
    """
    # Validate org access
    get_current_org_id(org_id, db)
    
    # Total signals
    total_signals = db.query(Signal).filter(Signal.org_id == org_id).count()
    
    # Signals by severity
    severity_counts = db.query(
        Signal.severity,
        func.count(Signal.id).label("count")
    ).filter(Signal.org_id == org_id).group_by(Signal.severity).all()
    
    signals_by_severity = {row.severity: row.count for row in severity_counts}
    
    # Signals by category
    category_counts = db.query(
        Signal.category,
        func.count(Signal.id).label("count")
    ).filter(Signal.org_id == org_id).group_by(Signal.category).all()
    
    signals_by_category = {row.category: row.count for row in category_counts}
    
    # Total assets
    total_assets = db.query(Asset).filter(Asset.org_id == org_id).count()
    
    # Total scans
    total_scans = db.query(Scan).filter(Scan.org_id == org_id).count()
    
    # Last 7 scans for risk trend sparkline
    recent_scans = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).limit(7).all()
    
    risk_trend = [
        {
            "score": scan.risk_score,
            "date": scan.created_at.isoformat() if scan.created_at else None
        }
        for scan in reversed(recent_scans)  # Oldest first for sparkline
    ]
    
    # Last scan timestamp and AI exposure
    last_scan = recent_scans[0] if recent_scans else None
    last_scan_at = last_scan.created_at if last_scan else None
    
    # Determine AI exposure level from most recent scan
    ai_exposure_level = "low"
    if last_scan and last_scan.scan_ai:
        ai_exposure_level = last_scan.scan_ai.ai_exposure_level
    
    # Top 5 high-severity signals
    high_sev_signals = db.query(Signal).filter(
        Signal.org_id == org_id,
        Signal.severity.in_(["high", "critical"])
    ).order_by(desc(Signal.created_at)).limit(5).all()
    
    top_signals = [signal_to_read(s, db) for s in high_sev_signals]
    
    # Top 3 recurring risks (signals that appear most frequently by title)
    recurring_risks_query = db.query(
        Signal.title,
        func.count(Signal.id).label("count")
    ).filter(
        Signal.org_id == org_id,
        Signal.severity.in_(["high", "critical"])
    ).group_by(Signal.title).order_by(desc("count")).limit(3).all()
    
    # Get actual signal objects for recurring risks
    top_recurring_risks = []
    for row in recurring_risks_query:
        signal = db.query(Signal).filter(
            Signal.org_id == org_id,
            Signal.title == row.title
        ).order_by(desc(Signal.created_at)).first()
        if signal:
            top_recurring_risks.append(signal_to_read(signal, db))
    
    return EnhancedOrgSummary(
        org_id=org_id,
        total_signals=total_signals,
        signals_by_severity=signals_by_severity,
        signals_by_category=signals_by_category,
        total_assets=total_assets,
        last_scan_at=last_scan_at,
        top_high_severity_signals=top_signals,
        total_scans=total_scans,
        risk_trend=risk_trend,
        categories_heatmap=signals_by_category,  # Same as signals_by_category
        ai_exposure_level=ai_exposure_level,
        top_recurring_risks=top_recurring_risks,
    )


@router.get("/{org_id}/assets")
async def get_org_assets(
    org_id: str,
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get assets for an organization.
    """
    get_current_org_id(org_id, db)
    
    query = db.query(Asset).filter(Asset.org_id == org_id)
    
    if asset_type:
        query = query.filter(Asset.type == asset_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    assets = query.order_by(desc(Asset.updated_at)).offset(offset).limit(page_size).all()
    
    return {
        "assets": [
            {
                "id": a.id,
                "type": a.type,
                "name": a.name,
                "properties": a.properties,
                "risk_tags": a.risk_tags,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
            }
            for a in assets
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (offset + len(assets)) < total,
    }
