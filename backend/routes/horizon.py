"""
Horizon Routes (Phase 2 Extended)

Organization-level security intelligence endpoints:
- GET /api/v1/org/{org_id}/horizon - Get Horizon dashboard data
- GET /api/v1/org/{org_id}/overview - Get organization overview (executive dashboard)
- GET /api/v1/org/{org_id}/weekly-brief - Get weekly security brief
- GET /api/v1/org/{org_id}/risk-timeline - Get weekly risk timeline
- POST /api/v1/org/{org_id}/weekly-brief/send - Send weekly brief via email
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import Organization, Scan, ScanAI, SecurityDecision, Signal, Asset
from ..schemas import (
    AIPosture,
    AssetRiskSummary,
    AssetWithRisk,
    DecisionSummary,
    HorizonResponse,
    OrgOverview,
    SendBriefRequest,
    SendBriefResponse,
    WeeklyBriefResponse,
)
from ..services.weekly_brief_service import build_weekly_brief, enhance_with_gemini
from ..services.pdf_generator import generate_brief_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org", tags=["horizon"])


# =============================================================================
# Phase 2 Schemas
# =============================================================================

class RiskTimelinePoint(BaseModel):
    """Single point in the risk timeline."""
    week_start: str = Field(..., description="Week start date YYYY-MM-DD")
    risk_score: int = Field(..., ge=0, le=100, description="Max risk score for that week")
    ai_score: Optional[int] = Field(None, description="Max AI score for that week")
    delta_from_prev: Optional[int] = Field(None, description="Change from previous week")


class RiskTimelineResponse(BaseModel):
    """Risk timeline response."""
    org_id: str
    points: List[RiskTimelinePoint]
    last_updated: Optional[datetime] = None


# =============================================================================
# Helper Functions
# =============================================================================

def get_current_org_id(org_id: str, db: Session) -> str:
    """Validate org exists and return org_id."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_id


def calculate_ai_posture(db: Session, org_id: str) -> AIPosture:
    """Calculate AI posture from latest scan data."""
    # Get latest scan with AI data
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    if not latest_scan or not latest_scan.scan_ai:
        return AIPosture(score=0, trend=0, status="clean")
    
    scan_ai = latest_scan.scan_ai
    score = scan_ai.ai_score or 0
    
    # Determine status based on score thresholds
    if score <= 20:
        status = "clean"
    elif score <= 50:
        status = "warning"
    else:
        status = "critical"
    
    # Calculate trend from previous scan
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    previous_scan = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at < week_ago
    ).order_by(desc(Scan.created_at)).first()
    
    trend = 0
    if previous_scan and previous_scan.scan_ai:
        previous_score = previous_scan.scan_ai.ai_score or 0
        trend = score - previous_score
    
    return AIPosture(score=score, trend=trend, status=status)


def get_latest_risk_score(db: Session, org_id: str) -> tuple[int, int]:
    """Get current risk score and trend."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    
    # Get latest scan
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    if not latest_scan:
        return 0, 0
    
    current_score = latest_scan.risk_score
    
    # Get previous scan for trend
    previous_scan = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at < week_ago
    ).order_by(desc(Scan.created_at)).first()
    
    trend = 0
    if previous_scan:
        trend = current_score - previous_scan.risk_score
    
    return current_score, trend


def get_top_decisions(db: Session, org_id: str, limit: int = 3) -> list[DecisionSummary]:
    """Get top pending decisions for the org."""
    decisions = db.query(SecurityDecision).join(
        Scan, SecurityDecision.scan_id == Scan.id
    ).filter(
        Scan.org_id == org_id,
        SecurityDecision.status.in_(['pending', 'in_progress'])
    ).order_by(SecurityDecision.priority).limit(limit).all()
    
    return [
        DecisionSummary(
            id=d.id,
            title=d.title,
            effort_estimate=d.effort_estimate,
            estimated_risk_reduction=d.estimated_risk_reduction,
            priority=d.priority,
            status=d.status,
        )
        for d in decisions
    ]


def count_critical_signals(db: Session, org_id: str) -> int:
    """Count unresolved critical/high severity signals."""
    return db.query(Signal).filter(
        Signal.org_id == org_id,
        Signal.severity.in_(['critical', 'high'])
    ).count()


def get_top_decisions_with_business(db: Session, org_id: str, limit: int = 5) -> list[DecisionSummary]:
    """Get top pending decisions with business impact for the org."""
    decisions = db.query(SecurityDecision).join(
        Scan, SecurityDecision.scan_id == Scan.id
    ).filter(
        Scan.org_id == org_id,
        SecurityDecision.status.in_(['pending', 'in_progress'])
    ).order_by(SecurityDecision.priority).limit(limit).all()
    
    result = []
    for d in decisions:
        # Get asset name if linked
        asset_name = None
        if d.asset_id:
            asset = db.query(Asset).filter(Asset.id == d.asset_id).first()
            if asset:
                asset_name = asset.name
        
        result.append(DecisionSummary(
            id=d.id,
            title=d.title,
            effort_estimate=d.effort_estimate,
            estimated_risk_reduction=d.estimated_risk_reduction,
            priority=d.priority,
            status=d.status,
            business_impact=d.business_impact,
            confidence_score=d.confidence_score or 0.8,
            asset_name=asset_name,
        ))
    
    return result


def calculate_org_risk_score(db: Session, org_id: str) -> tuple[int, int, int, int]:
    """
    Calculate weighted aggregate risk score for the organization.
    
    Returns: (total_risk, trend_30d, trend_60d, trend_90d)
    """
    now = datetime.now(timezone.utc)
    
    # Get all active assets with their risk scores
    assets = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.status == 'active',
        Asset.last_risk_score.isnot(None),
    ).all()
    
    if not assets:
        # Fallback to latest scan
        latest_scan = db.query(Scan).filter(
            Scan.org_id == org_id
        ).order_by(desc(Scan.created_at)).first()
        
        if not latest_scan:
            return 0, 0, 0, 0
        
        current_score = latest_scan.risk_score
        
        # Get 30d ago scan
        scan_30d = db.query(Scan).filter(
            Scan.org_id == org_id,
            Scan.created_at <= now - timedelta(days=30)
        ).order_by(desc(Scan.created_at)).first()
        
        # Get 60d ago scan
        scan_60d = db.query(Scan).filter(
            Scan.org_id == org_id,
            Scan.created_at <= now - timedelta(days=60)
        ).order_by(desc(Scan.created_at)).first()
        
        # Get 90d ago scan
        scan_90d = db.query(Scan).filter(
            Scan.org_id == org_id,
            Scan.created_at <= now - timedelta(days=90)
        ).order_by(desc(Scan.created_at)).first()
        
        trend_30d = (current_score - scan_30d.risk_score) if scan_30d else 0
        trend_60d = (current_score - scan_60d.risk_score) if scan_60d else 0
        trend_90d = (current_score - scan_90d.risk_score) if scan_90d else 0
        
        return current_score, trend_30d, trend_60d, trend_90d
    
    # Weighted average
    total_weight = sum(a.risk_weight for a in assets)
    if total_weight == 0:
        return 0, 0, 0, 0
    
    weighted_sum = sum(a.last_risk_score * a.risk_weight for a in assets if a.last_risk_score)
    current_score = int(weighted_sum / total_weight)
    
    # For trends, use scan history
    scan_30d = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at <= now - timedelta(days=30)
    ).order_by(desc(Scan.created_at)).first()
    
    scan_60d = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at <= now - timedelta(days=60)
    ).order_by(desc(Scan.created_at)).first()
    
    scan_90d = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at <= now - timedelta(days=90)
    ).order_by(desc(Scan.created_at)).first()
    
    trend_30d = (current_score - scan_30d.risk_score) if scan_30d else 0
    trend_60d = (current_score - scan_60d.risk_score) if scan_60d else 0
    trend_90d = (current_score - scan_90d.risk_score) if scan_90d else 0
    
    return current_score, trend_30d, trend_60d, trend_90d


def get_top_risky_assets(db: Session, org_id: str, limit: int = 3) -> List[AssetWithRisk]:
    """Get top risky assets."""
    assets = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.status == 'active',
        Asset.last_risk_score.isnot(None),
    ).order_by(desc(Asset.last_risk_score)).limit(limit).all()
    
    result = []
    for a in assets:
        # Count signals
        signal_count = db.query(Signal).filter(Signal.asset_id == a.id).count()
        
        result.append(AssetWithRisk(
            id=a.id,
            org_id=a.org_id,
            type=a.type,
            name=a.name,
            external_id=a.external_id,
            properties=a.properties or {},
            risk_tags=a.risk_tags or [],
            risk_weight=a.risk_weight,
            scan_frequency=a.scan_frequency,
            last_scan_at=a.last_scan_at,
            next_scan_at=a.next_scan_at,
            last_risk_score=a.last_risk_score,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
            current_risk_score=a.last_risk_score,
            risk_trend=None,
            signal_count=signal_count,
        ))
    
    return result


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{org_id}/overview", response_model=OrgOverview)
async def get_org_overview(
    org_id: str,
    db: Session = Depends(get_db),
):
    """
    Get organization overview for executive dashboard.
    
    Returns aggregated security posture across all assets:
    - Total weighted risk score
    - 30-day, 60-day, and 90-day risk trends
    - Top 3 risky assets
    - AI posture summary
    - Unresolved decisions count and breakdown by status
    - This week's priority decisions
    - Asset breakdown by type
    - Usage limits and plan info
    - Recommended next action
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Calculate aggregate risk
    total_risk, trend_30d, trend_60d, trend_90d = calculate_org_risk_score(db, org_id)
    
    # Get top risky assets
    top_assets = get_top_risky_assets(db, org_id, limit=3)
    
    # Get AI posture
    ai_posture = calculate_ai_posture(db, org_id)
    
    # Count unresolved decisions and get breakdown by status
    all_decisions = db.query(SecurityDecision).join(
        Scan, SecurityDecision.scan_id == Scan.id
    ).filter(
        Scan.org_id == org_id
    ).all()
    
    decisions_by_status = {
        'pending': 0,
        'accepted': 0,
        'in_progress': 0,
        'resolved': 0,
        'verified': 0
    }
    for d in all_decisions:
        if d.status in decisions_by_status:
            decisions_by_status[d.status] += 1
    
    unresolved_count = decisions_by_status['pending'] + decisions_by_status['accepted'] + decisions_by_status['in_progress']
    
    # Get this week's decisions
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    decisions_this_week = get_top_decisions_with_business(db, org_id, limit=5)
    
    # Asset counts by type
    asset_counts = db.query(
        Asset.type,
        func.count(Asset.id).label('count')
    ).filter(
        Asset.org_id == org_id,
        Asset.status == 'active'
    ).group_by(Asset.type).all()
    
    assets_by_type = {row.type: row.count for row in asset_counts}
    total_assets = sum(assets_by_type.values())
    
    # Last updated
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    # Determine next action based on current state
    next_action = _determine_next_action(
        total_risk=total_risk,
        unresolved_count=unresolved_count,
        ai_posture=ai_posture,
        total_assets=total_assets,
        latest_scan=latest_scan,
        decisions_this_week=decisions_this_week
    )
    
    return OrgOverview(
        org_id=org_id,
        org_name=org.name,
        total_risk_score=total_risk,
        risk_trend_30d=trend_30d,
        risk_trend_60d=trend_60d,
        risk_trend_90d=trend_90d,
        top_risky_assets=top_assets,
        ai_posture=ai_posture,
        unresolved_decisions_count=unresolved_count,
        decisions_by_status=decisions_by_status,
        decisions_this_week=decisions_this_week,
        assets_by_type=assets_by_type,
        total_assets=total_assets,
        total_scans_this_month=org.scans_this_month,
        scans_limit=org.scans_limit,
        plan=org.plan,
        last_updated=latest_scan.created_at if latest_scan else None,
        next_action=next_action,
    )


def _determine_next_action(
    total_risk: int,
    unresolved_count: int,
    ai_posture: AIPosture,
    total_assets: int,
    latest_scan,
    decisions_this_week: list
) -> str:
    """
    Determine the recommended next action for the user.
    Logic is deterministic and based on current security state.
    """
    now = datetime.now(timezone.utc)
    
    # Priority 1: No assets scanned yet
    if total_assets == 0 or latest_scan is None:
        return "Add your first asset to start monitoring your security posture"
    
    # Priority 2: Critical AI exposure
    if ai_posture.status == "critical":
        return "Address critical AI exposure - exposed API keys or agent frameworks detected"
    
    # Priority 3: High risk score
    if total_risk >= 70:
        return "Review high-risk findings and address the top security decision"
    
    # Priority 4: Pending decisions
    if unresolved_count > 0 and decisions_this_week:
        top_decision = decisions_this_week[0]
        return f"Complete '{top_decision.title}' - estimated {top_decision.effort_estimate}"
    
    # Priority 5: Stale scan
    if latest_scan:
        scan_age = now - (latest_scan.created_at.replace(tzinfo=timezone.utc) if latest_scan.created_at.tzinfo is None else latest_scan.created_at)
        if scan_age > timedelta(days=7):
            return "Run a new scan - your last assessment was over a week ago"
    
    # Priority 6: AI exposure warning
    if ai_posture.status == "warning":
        return "Review AI tool usage - moderate exposure detected"
    
    # Default: All clear
    return "Your security posture is healthy. Keep monitoring for new signals."


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{org_id}/horizon", response_model=HorizonResponse)
async def get_horizon_data(
    org_id: str,
    db: Session = Depends(get_db),
):
    """
    Get Horizon dashboard data for an organization.
    
    Returns aggregated security posture data:
    - Current risk score and trend
    - Top pending decisions
    - Unresolved critical signals count
    - AI exposure posture
    """
    # Validate org exists
    get_current_org_id(org_id, db)
    
    # Get risk score and trend
    current_score, risk_trend = get_latest_risk_score(db, org_id)
    
    # Get top pending decisions
    top_decisions = get_top_decisions(db, org_id, limit=3)
    
    # Count critical signals
    critical_count = count_critical_signals(db, org_id)
    
    # Calculate AI posture
    ai_posture = calculate_ai_posture(db, org_id)
    
    # Get last updated timestamp
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    last_updated = latest_scan.created_at if latest_scan else None
    
    # Get assets summary
    assets_summary = get_assets_summary(db, org_id, limit=8)

    return HorizonResponse(
        current_risk_score=current_score,
        risk_trend=risk_trend,
        top_decisions=top_decisions,
        unresolved_critical_signals=critical_count,
        ai_posture=ai_posture,
        last_updated=last_updated,
        assets_summary=assets_summary,
    )


@router.get("/{org_id}/risk-timeline", response_model=RiskTimelineResponse)
async def get_risk_timeline(
    org_id: str,
    weeks: int = 12,
    db: Session = Depends(get_db),
):
    """
    Get weekly risk timeline for an organization.
    
    Returns weekly risk score points for the last N weeks (default 12).
    Each point includes:
    - week_start: Monday of that week
    - risk_score: Maximum risk score from scans that week
    - ai_score: Maximum AI score from scans that week
    - delta_from_prev: Change from previous week
    
    This endpoint is deterministic and does not use any LLM.
    """
    # Validate org exists
    get_current_org_id(org_id, db)
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    weeks = min(max(weeks, 4), 52)  # Clamp between 4 and 52 weeks
    start_date = now - timedelta(weeks=weeks)
    
    # Get all scans in the time range
    scans = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at >= start_date
    ).order_by(Scan.created_at).all()
    
    # Group by week (Monday-based)
    weekly_data = {}
    
    for scan in scans:
        # Get Monday of that week
        scan_date = scan.created_at
        if scan_date.tzinfo is None:
            scan_date = scan_date.replace(tzinfo=timezone.utc)
        week_start = (scan_date - timedelta(days=scan_date.weekday())).date()
        
        if week_start not in weekly_data:
            weekly_data[week_start] = {
                'risk_scores': [],
                'ai_scores': [],
            }
        
        weekly_data[week_start]['risk_scores'].append(scan.risk_score)
        if scan.scan_ai and scan.scan_ai.ai_score is not None:
            weekly_data[week_start]['ai_scores'].append(scan.scan_ai.ai_score)
    
    # Build timeline points
    points = []
    sorted_weeks = sorted(weekly_data.keys())
    prev_score = None
    
    for week_start in sorted_weeks:
        data = weekly_data[week_start]
        risk_score = max(data['risk_scores']) if data['risk_scores'] else 0
        ai_score = max(data['ai_scores']) if data['ai_scores'] else None
        
        delta = (risk_score - prev_score) if prev_score is not None else None
        prev_score = risk_score
        
        points.append(RiskTimelinePoint(
            week_start=week_start.isoformat(),
            risk_score=risk_score,
            ai_score=ai_score,
            delta_from_prev=delta,
        ))
    
    # Get last updated
    last_updated = scans[-1].created_at if scans else None
    
    return RiskTimelineResponse(
        org_id=org_id,
        points=points,
        last_updated=last_updated,
    )


@router.get("/{org_id}/weekly-brief", response_model=WeeklyBriefResponse)
async def get_weekly_brief(
    org_id: str,
    include_explanation: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get weekly security brief for an organization.
    
    Returns a human-readable security brief with:
    - Headline summarizing the week
    - Top changes (resolved issues)
    - Top 3 priority actions
    - AI exposure summary
    - Optional plain English explanation (via Gemini)
    
    Args:
        org_id: Organization ID
        include_explanation: If True, includes Gemini-generated explanation
    """
    # Validate org exists
    get_current_org_id(org_id, db)
    
    # Build brief using deterministic logic
    brief = build_weekly_brief(db, org_id)
    
    # Optionally enhance with Gemini explanation
    if include_explanation:
        brief = await enhance_with_gemini(brief)
    
    return brief


def get_assets_summary(db: Session, org_id: str, limit: int = 8) -> List[AssetRiskSummary]:
    """
    Get per-asset risk summary for the organization.
    
    Computes risk score and trend for each unique domain scanned.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    
    # Get unique domains from org scans
    domains = db.query(Scan.domain).filter(
        Scan.org_id == org_id
    ).distinct().limit(limit).all()
    
    summaries = []
    
    for (domain,) in domains:
        # Get latest scan for this domain
        latest_scan = db.query(Scan).filter(
            Scan.org_id == org_id,
            Scan.domain == domain
        ).order_by(desc(Scan.created_at)).first()
        
        if not latest_scan:
            continue
        
        # Get previous scan for trend
        previous_scan = db.query(Scan).filter(
            Scan.org_id == org_id,
            Scan.domain == domain,
            Scan.created_at < week_ago
        ).order_by(desc(Scan.created_at)).first()
        
        trend = 0
        if previous_scan:
            trend = latest_scan.risk_score - previous_scan.risk_score
        
        summaries.append(AssetRiskSummary(
            asset_id=latest_scan.id,  # Use scan ID as asset reference
            asset_type="domain",
            name=domain,
            risk_score=latest_scan.risk_score,
            trend=trend,
        ))
    
    # Sort by risk score descending
    summaries.sort(key=lambda x: x.risk_score, reverse=True)
    
    return summaries


def validate_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@router.post("/{org_id}/weekly-brief/send", response_model=SendBriefResponse)
async def send_weekly_brief(
    org_id: str,
    request: SendBriefRequest,
    db: Session = Depends(get_db),
):
    """
    Send weekly security brief via email.
    
    Generates PDF attachment and sends via Resend.
    
    Requires RESEND_API_KEY environment variable.
    
    Args:
        org_id: Organization ID
        request: Email recipient and options
    """
    # Validate RESEND_API_KEY exists
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=400,
            detail="RESEND_API_KEY not configured. Please set this environment variable to enable email delivery."
        )
    
    # Validate email format
    if not validate_email(request.to):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid email address: {request.to}"
        )
    
    # Validate org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org_name = org.name or org.primary_domain
    
    # Build brief
    brief = build_weekly_brief(db, org_id)
    
    # Optionally enhance with Gemini
    if request.include_explanation and settings.gemini_api_key:
        brief = await enhance_with_gemini(brief)
    
    # Generate PDF
    pdf_bytes = generate_brief_pdf(brief, org_name)
    
    # Build HTML email
    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #7c3aed;">Weekly Security Brief</h1>
        <p style="color: #64748b;">{org_name}</p>
        
        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h2 style="margin: 0; color: #1e293b;">{brief.headline}</h2>
        </div>
        
        {"<h3>Completed This Week</h3><ul>" + "".join(f"<li>{c}</li>" for c in brief.top_changes[:5]) + "</ul>" if brief.top_changes else ""}
        
        {"<h3>Priority Actions</h3><ol>" + "".join(f"<li><strong>{a.title}</strong> ({a.effort_estimate})</li>" for a in brief.top_3_actions) + "</ol>" if brief.top_3_actions else ""}
        
        <h3>AI Exposure</h3>
        <p>{brief.ai_exposure_summary}</p>
        
        {f'<div style="background: #faf5ff; border-left: 4px solid #7c3aed; padding: 12px; margin: 20px 0;"><strong>Analysis:</strong><br>{brief.explanation}</div>' if brief.explanation else ''}
        
        <p style="color: #94a3b8; font-size: 12px;">Confidence: {brief.confidence_level.upper()}</p>
        
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        <p style="color: #94a3b8; font-size: 12px;">
            Generated by ThreatVeil • <a href="https://threatveil.com" style="color: #7c3aed;">View Dashboard</a>
        </p>
    </body>
    </html>
    """
    
    # Send via Resend
    import httpx
    import base64
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": "ThreatVeil <noreply@threatveil.com>",
                    "to": [request.to],
                    "subject": f"Weekly Security Brief - {org_name}",
                    "html": html_content,
                    "attachments": [
                        {
                            "filename": "security-brief.pdf",
                            "content": base64.b64encode(pdf_bytes).decode("utf-8"),
                        }
                    ],
                },
            )
            
            if response.status_code not in (200, 201):
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to send email via Resend: {response.status_code}"
                )
            
            data = response.json()
            message_id = data.get("id", "unknown")
            
            logger.info(f"Weekly brief sent to {request.to}, message_id={message_id}")
            
            return SendBriefResponse(
                message_id=message_id,
                status="sent",
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Email service timeout")
    except Exception as e:
        logger.error(f"Error sending weekly brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")
