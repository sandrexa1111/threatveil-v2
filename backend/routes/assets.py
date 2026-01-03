"""
Asset Management Routes

CRUD operations for organization assets with support for:
- Domain, GitHub org, cloud account, and SaaS vendor types
- Scan scheduling and frequency management
- Manual scan triggering
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Asset, Organization, Signal, Scan, ScanSchedule, AuditLog, SecurityDecision
from ..schemas import (
    AssetCreate,
    AssetUpdate,
    AssetRead,
    AssetWithRisk,
    AssetListResponse,
)

router = APIRouter(prefix="/api/v1/org/{org_id}/assets", tags=["assets"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_org_or_404(org_id: str, db: Session) -> Organization:
    """Get organization or raise 404."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def calculate_next_scan(frequency: str, from_time: datetime = None) -> datetime:
    """Calculate next scan time based on frequency."""
    now = from_time or datetime.utcnow()
    
    if frequency == "daily":
        return now + timedelta(hours=24)
    elif frequency == "weekly":
        return now + timedelta(days=7)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    else:  # manual
        return None


def asset_to_read(asset: Asset) -> AssetRead:
    """Convert Asset model to AssetRead schema."""
    return AssetRead(
        id=asset.id,
        org_id=asset.org_id,
        type=asset.type,
        name=asset.name,
        external_id=asset.external_id,
        properties=asset.properties or {},
        risk_tags=asset.risk_tags or [],
        risk_weight=asset.risk_weight,
        scan_frequency=asset.scan_frequency,
        last_scan_at=asset.last_scan_at,
        next_scan_at=asset.next_scan_at,
        last_risk_score=asset.last_risk_score,
        status=asset.status,
        owner_email=asset.owner_email,
        priority=asset.priority or "normal",
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def asset_to_with_risk(asset: Asset, db: Session) -> AssetWithRisk:
    """Convert Asset model to AssetWithRisk with computed fields."""
    # Count signals for this asset
    signal_count = db.query(Signal).filter(Signal.asset_id == asset.id).count()
    
    # Get risk trend if we have multiple scans
    risk_trend = None
    if asset.last_risk_score is not None:
        # Try to find previous risk score
        previous_scan = db.query(Scan).filter(
            Scan.org_id == asset.org_id,
            Scan.domain == asset.name,
            Scan.created_at < (asset.last_scan_at or datetime.utcnow())
        ).order_by(desc(Scan.created_at)).first()
        
        if previous_scan:
            risk_trend = asset.last_risk_score - previous_scan.risk_score
    
    return AssetWithRisk(
        id=asset.id,
        org_id=asset.org_id,
        type=asset.type,
        name=asset.name,
        external_id=asset.external_id,
        properties=asset.properties or {},
        risk_tags=asset.risk_tags or [],
        risk_weight=asset.risk_weight,
        scan_frequency=asset.scan_frequency,
        last_scan_at=asset.last_scan_at,
        next_scan_at=asset.next_scan_at,
        last_risk_score=asset.last_risk_score,
        status=asset.status,
        owner_email=asset.owner_email,
        priority=asset.priority or "normal",
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        current_risk_score=asset.last_risk_score,
        risk_trend=risk_trend,
        signal_count=signal_count,
    )


def log_action(
    db: Session,
    org_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict = None,
    user_id: str = None,
):
    """Create an audit log entry."""
    log = AuditLog(
        org_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log)


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.get("", response_model=AssetListResponse)
async def list_assets(
    org_id: str,
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    status: Optional[str] = Query("active", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all assets for an organization with optional filters."""
    get_org_or_404(org_id, db)
    
    query = db.query(Asset).filter(Asset.org_id == org_id)
    
    if asset_type:
        query = query.filter(Asset.type == asset_type)
    if status:
        query = query.filter(Asset.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    assets = query.order_by(desc(Asset.updated_at)).offset(offset).limit(page_size).all()
    
    return AssetListResponse(
        assets=[asset_to_read(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(assets)) < total,
    )


@router.post("", response_model=AssetRead, status_code=201)
async def create_asset(
    org_id: str,
    asset: AssetCreate,
    db: Session = Depends(get_db),
):
    """Create a new asset for an organization."""
    org = get_org_or_404(org_id, db)
    
    # Validate asset type
    valid_types = {"domain", "github_org", "cloud_account", "saas_vendor"}
    if asset.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid asset type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate scan frequency
    valid_frequencies = {"daily", "weekly", "monthly", "manual"}
    if asset.scan_frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scan frequency. Must be one of: {', '.join(valid_frequencies)}"
        )
    
    # Check for duplicate
    existing = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.type == asset.type,
        Asset.name == asset.name,
        Asset.status != "deleted",
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Asset '{asset.name}' of type '{asset.type}' already exists"
        )
    
    # Create asset
    new_asset = Asset(
        org_id=org_id,
        type=asset.type,
        name=asset.name,
        external_id=asset.external_id,
        properties=asset.properties,
        risk_tags=asset.risk_tags,
        risk_weight=asset.risk_weight,
        scan_frequency=asset.scan_frequency,
        next_scan_at=calculate_next_scan(asset.scan_frequency),
        status="active",
    )
    
    db.add(new_asset)
    
    # Create scan schedule if not manual
    if asset.scan_frequency != "manual":
        schedule = ScanSchedule(
            org_id=org_id,
            asset_id=new_asset.id,
            frequency=asset.scan_frequency,
            next_run_at=new_asset.next_scan_at,
            status="active",
        )
        db.add(schedule)
    
    # Log action
    log_action(db, org_id, "asset_created", "asset", new_asset.id, {
        "type": asset.type,
        "name": asset.name,
        "scan_frequency": asset.scan_frequency,
    })
    
    db.commit()
    db.refresh(new_asset)
    
    return asset_to_read(new_asset)


@router.get("/{asset_id}", response_model=AssetWithRisk)
async def get_asset(
    org_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific asset with risk information."""
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset_to_with_risk(asset, db)


@router.put("/{asset_id}", response_model=AssetRead)
async def update_asset(
    org_id: str,
    asset_id: str,
    update: AssetUpdate,
    db: Session = Depends(get_db),
):
    """Update an asset."""
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    
    # Handle scan frequency change
    if "scan_frequency" in update_data:
        new_freq = update_data["scan_frequency"]
        valid_frequencies = {"daily", "weekly", "monthly", "manual"}
        if new_freq not in valid_frequencies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scan frequency. Must be one of: {', '.join(valid_frequencies)}"
            )
        
        # Update next scan time
        asset.next_scan_at = calculate_next_scan(new_freq)
        
        # Update or create schedule
        schedule = db.query(ScanSchedule).filter(
            ScanSchedule.asset_id == asset_id
        ).first()
        
        if new_freq == "manual":
            if schedule:
                schedule.status = "paused"
        else:
            if schedule:
                schedule.frequency = new_freq
                schedule.next_run_at = asset.next_scan_at
                schedule.status = "active"
            else:
                schedule = ScanSchedule(
                    org_id=org_id,
                    asset_id=asset_id,
                    frequency=new_freq,
                    next_run_at=asset.next_scan_at,
                    status="active",
                )
                db.add(schedule)
    
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    # Log action
    log_action(db, org_id, "asset_updated", "asset", asset_id, update_data)
    
    db.commit()
    db.refresh(asset)
    
    return asset_to_read(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    org_id: str,
    asset_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    db: Session = Depends(get_db),
):
    """Delete an asset (soft delete by default)."""
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if hard_delete:
        db.delete(asset)
        log_action(db, org_id, "asset_deleted_hard", "asset", asset_id, {"name": asset.name})
    else:
        asset.status = "deleted"
        # Pause schedule
        schedule = db.query(ScanSchedule).filter(ScanSchedule.asset_id == asset_id).first()
        if schedule:
            schedule.status = "paused"
        log_action(db, org_id, "asset_deleted_soft", "asset", asset_id, {"name": asset.name})
    
    db.commit()


@router.post("/{asset_id}/scan", status_code=202)
async def trigger_asset_scan(
    org_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Trigger a manual scan for an asset."""
    org = get_org_or_404(org_id, db)
    
    # Check usage limits
    if org.scans_this_month >= org.scans_limit and org.plan == "free":
        raise HTTPException(
            status_code=402,
            detail=f"Scan limit reached ({org.scans_limit} scans/month on free plan). Upgrade to continue."
        )
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
        Asset.status == "active",
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found or inactive")
    
    # Only domain and github_org can be scanned
    if asset.type not in ("domain", "github_org"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot scan asset type '{asset.type}'. Only domains and GitHub orgs are scannable."
        )
    
    # Log action and return
    log_action(db, org_id, "scan_triggered", "asset", asset_id, {"asset_name": asset.name})
    
    db.commit()
    
    # Note: Actual scan should be triggered via a task queue
    # For now, return a pending response
    return {
        "message": f"Scan queued for asset '{asset.name}'",
        "asset_id": asset_id,
        "asset_name": asset.name,
        "asset_type": asset.type,
        "status": "queued",
    }


@router.get("/stats/by-type")
async def get_assets_by_type(
    org_id: str,
    db: Session = Depends(get_db),
):
    """Get asset counts grouped by type."""
    get_org_or_404(org_id, db)
    
    counts = db.query(
        Asset.type,
        func.count(Asset.id).label("count")
    ).filter(
        Asset.org_id == org_id,
        Asset.status == "active",
    ).group_by(Asset.type).all()
    
    return {
        "by_type": {row.type: row.count for row in counts},
        "total": sum(row.count for row in counts),
    }


# =============================================================================
# Asset Detail Endpoints (Phase 3)
# =============================================================================

@router.get("/{asset_id}/risk-history")
async def get_asset_risk_history(
    org_id: str,
    asset_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of scan points to return"),
    db: Session = Depends(get_db),
):
    """
    Get risk score history for an asset.
    
    Returns the last N scans with risk scores for this asset's domain.
    """
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get scan history for this domain
    scans = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.domain == asset.name,
    ).order_by(desc(Scan.created_at)).limit(limit).all()
    
    history = []
    for scan in scans:
        history.append({
            "scan_id": scan.id,
            "risk_score": scan.risk_score,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
            "ai_score": scan.scan_ai.ai_score if scan.scan_ai else None,
        })
    
    return {
        "asset_id": asset_id,
        "asset_name": asset.name,
        "history": list(reversed(history)),  # Oldest first for charting
        "total_scans": len(history),
    }


@router.get("/{asset_id}/recurring-signals")
async def get_asset_recurring_signals(
    org_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    Get recurring signals grouped by category for an asset.
    
    Identifies signals that keep appearing across multiple scans.
    """
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get all signals for this asset
    signals = db.query(Signal).filter(
        Signal.asset_id == asset_id,
    ).all()
    
    # Group by category and type
    from collections import defaultdict
    grouped = defaultdict(lambda: {"count": 0, "severities": defaultdict(int), "signals": []})
    
    for s in signals:
        key = f"{s.category}:{s.type}"
        grouped[key]["count"] += 1
        grouped[key]["severities"][s.severity] += 1
        if len(grouped[key]["signals"]) < 3:  # Keep top 3 examples
            grouped[key]["signals"].append({
                "id": s.id,
                "title": s.title,
                "severity": s.severity,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
    
    # Convert to list sorted by count
    recurring = []
    for key, data in grouped.items():
        if data["count"] >= 2:  # Only include if seen 2+ times
            category, signal_type = key.split(":", 1)
            recurring.append({
                "category": category,
                "type": signal_type,
                "occurrence_count": data["count"],
                "severity_breakdown": dict(data["severities"]),
                "examples": data["signals"],
            })
    
    recurring.sort(key=lambda x: x["occurrence_count"], reverse=True)
    
    return {
        "asset_id": asset_id,
        "asset_name": asset.name,
        "recurring_signals": recurring[:10],  # Top 10 recurring
        "total_signal_count": len(signals),
    }


@router.get("/{asset_id}/decisions")
async def get_asset_decisions(
    org_id: str,
    asset_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """
    Get security decisions linked to an asset.
    
    Returns all decisions that were generated for this asset's scans.
    """
    get_org_or_404(org_id, db)
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org_id,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get all scans for this asset
    scan_ids = db.query(Scan.id).filter(
        Scan.org_id == org_id,
        Scan.domain == asset.name,
    ).all()
    scan_id_list = [s[0] for s in scan_ids]
    
    # Get decisions for these scans
    query = db.query(SecurityDecision).filter(
        SecurityDecision.scan_id.in_(scan_id_list)
    )
    
    if status:
        query = query.filter(SecurityDecision.status == status)
    
    decisions = query.order_by(desc(SecurityDecision.created_at)).all()
    
    # Format response
    decision_list = []
    for d in decisions:
        decision_list.append({
            "id": d.id,
            "title": d.title,
            "action_id": d.action_id,
            "status": d.status,
            "priority": d.priority,
            "effort_estimate": d.effort_estimate,
            "estimated_risk_reduction": d.estimated_risk_reduction,
            "confidence_score": d.confidence_score,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        })
    
    # Count by status
    status_counts = {
        "pending": 0,
        "accepted": 0,
        "in_progress": 0,
        "resolved": 0,
        "verified": 0,
    }
    for d in decisions:
        if d.status in status_counts:
            status_counts[d.status] += 1
    
    return {
        "asset_id": asset_id,
        "asset_name": asset.name,
        "decisions": decision_list,
        "total_count": len(decisions),
        "status_counts": status_counts,
    }

