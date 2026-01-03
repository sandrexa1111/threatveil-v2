"""
Weekly Brief Service

Deterministic weekly security brief builder with optional Gemini explanation layer.

This service:
1. Aggregates data from existing scans, signals, and decisions
2. Builds a structured brief using deterministic logic
3. Optionally enhances with Gemini for plain English explanation
4. Has fallback templates if Gemini is unavailable

AI GUARDRAILS:
- Gemini NEVER decides priority or computes scores
- Gemini ONLY rewrites deterministic output into plain English
- Every Gemini call has deterministic fallback
- Gemini calls are clamped to max length and never block API
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..models import Organization, Scan, ScanAI, SecurityDecision, Signal
from ..schemas import DecisionSummary, DecisionImpact, WeeklyBriefResponse
from ..config import settings


# =============================================================================
# Deterministic Brief Builder
# =============================================================================

def get_risk_delta(db: Session, org_id: str, days: int = 7) -> Tuple[int, int]:
    """
    Calculate risk score change over the specified period.
    
    Returns:
        (current_score, delta) where delta is current - previous
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=days)
    
    # Get latest scan
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    if not latest_scan:
        return 0, 0
    
    current_score = latest_scan.risk_score
    
    # Get scan from ~week ago (closest before the cutoff)
    previous_scan = db.query(Scan).filter(
        Scan.org_id == org_id,
        Scan.created_at < week_ago
    ).order_by(desc(Scan.created_at)).first()
    
    if not previous_scan:
        return current_score, 0
    
    delta = current_score - previous_scan.risk_score
    return current_score, delta


def get_resolved_decisions(db: Session, org_id: str, days: int = 7) -> List[SecurityDecision]:
    """Get decisions resolved in the past N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get resolved decisions from scans belonging to this org
    decisions = db.query(SecurityDecision).join(
        Scan, SecurityDecision.scan_id == Scan.id
    ).filter(
        Scan.org_id == org_id,
        SecurityDecision.status == 'resolved',
        SecurityDecision.resolved_at >= cutoff
    ).order_by(desc(SecurityDecision.resolved_at)).all()
    
    return decisions


def get_pending_decisions(db: Session, org_id: str, limit: int = 3) -> List[SecurityDecision]:
    """Get top pending decisions for the org."""
    decisions = db.query(SecurityDecision).join(
        Scan, SecurityDecision.scan_id == Scan.id
    ).filter(
        Scan.org_id == org_id,
        SecurityDecision.status.in_(['pending', 'in_progress'])
    ).order_by(SecurityDecision.priority).limit(limit).all()
    
    return decisions


def get_ai_exposure_summary(db: Session, org_id: str) -> str:
    """Generate AI exposure summary text from latest scan."""
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    if not latest_scan or not latest_scan.scan_ai:
        return "No AI exposure data available"
    
    scan_ai = latest_scan.scan_ai
    tools_count = len(scan_ai.ai_tools or [])
    keys_count = len(scan_ai.ai_keys or [])
    
    parts = []
    
    if tools_count > 0:
        parts.append(f"{tools_count} AI tool{'s' if tools_count > 1 else ''} detected")
    
    if keys_count > 0:
        parts.append(f"{keys_count} key leak{'s' if keys_count > 1 else ''} found")
    else:
        parts.append("no key leaks")
    
    if not parts:
        return "Clean AI posture - no exposures detected"
    
    return ", ".join(parts).capitalize()


def decision_to_summary(decision: SecurityDecision) -> DecisionSummary:
    """Convert SecurityDecision to DecisionSummary."""
    return DecisionSummary(
        id=decision.id,
        title=decision.title,
        effort_estimate=decision.effort_estimate,
        estimated_risk_reduction=decision.estimated_risk_reduction,
        priority=decision.priority,
        status=decision.status,
    )


def build_headline(current_score: int, delta: int, resolved_count: int) -> str:
    """Build deterministic headline based on metrics."""
    if delta < 0:
        return f"Risk decreased by {abs(delta)} points this week"
    elif delta > 0:
        return f"Risk increased by {delta} points - action needed"
    elif resolved_count > 0:
        return f"{resolved_count} security action{'s' if resolved_count > 1 else ''} completed this week"
    else:
        return f"Security posture stable at score {current_score}"


def build_confidence_level(
    has_recent_scan: bool,
    signal_count: int,
    decision_count: int
) -> str:
    """Determine confidence level based on data availability."""
    if not has_recent_scan:
        return "low"
    if signal_count >= 5 and decision_count >= 1:
        return "high"
    if signal_count >= 2 or decision_count >= 1:
        return "medium"
    return "low"


def get_decision_impacts(db: Session, org_id: str, days: int = 7) -> List[DecisionImpact]:
    """
    Get decision impacts for resolved decisions in the past N days.
    
    Returns list of DecisionImpact with actual risk delta and evidence signal IDs.
    """
    resolved = get_resolved_decisions(db, org_id, days)
    impacts = []
    
    for decision in resolved:
        # Calculate actual risk delta
        risk_delta = 0
        if decision.before_score is not None and decision.after_score is not None:
            risk_delta = decision.before_score - decision.after_score
        
        # Get related signals from the scan
        signal_ids = []
        if decision.scan_id:
            signals = db.query(Signal).filter(
                Signal.scan_id == decision.scan_id
            ).limit(5).all()
            signal_ids = [s.id for s in signals]
        
        # Get asset info from scan
        asset_id = None
        asset_name = None
        if decision.scan:
            asset_name = decision.scan.domain
        
        impacts.append(DecisionImpact(
            id=decision.id,
            title=decision.title,
            risk_delta_points=risk_delta,
            evidence_signal_ids=signal_ids,
            asset_id=asset_id,
            asset_name=asset_name,
        ))
    
    return impacts


def build_weekly_brief(db: Session, org_id: str) -> WeeklyBriefResponse:
    """
    Build weekly security brief using deterministic logic.
    
    This function aggregates existing data without any LLM calls.
    """
    # Get risk metrics
    current_score, delta = get_risk_delta(db, org_id)
    
    # Get resolved decisions for "top changes"
    resolved = get_resolved_decisions(db, org_id)
    top_changes = [f"Resolved: {d.title}" for d in resolved[:5]]
    
    # Get pending decisions for "top 3 actions"
    pending = get_pending_decisions(db, org_id, limit=3)
    top_3_actions = [decision_to_summary(d) for d in pending]
    
    # Get AI exposure summary
    ai_summary = get_ai_exposure_summary(db, org_id)
    
    # Build headline
    headline = build_headline(current_score, delta, len(resolved))
    
    # Get signal count for confidence
    signal_count = db.query(Signal).filter(Signal.org_id == org_id).count()
    
    # Determine confidence level
    latest_scan = db.query(Scan).filter(
        Scan.org_id == org_id
    ).order_by(desc(Scan.created_at)).first()
    
    has_recent_scan = latest_scan is not None and (
        datetime.now(timezone.utc) - latest_scan.created_at.replace(tzinfo=timezone.utc)
    ).days <= 7 if latest_scan else False
    
    confidence = build_confidence_level(has_recent_scan, signal_count, len(pending))
    
    # Get decision impacts
    decision_impacts = get_decision_impacts(db, org_id)
    
    return WeeklyBriefResponse(
        headline=headline,
        top_changes=top_changes,
        top_3_actions=top_3_actions,
        ai_exposure_summary=ai_summary,
        confidence_level=confidence,
        explanation=None,  # Will be populated by Gemini if enabled
        generated_at=datetime.now(timezone.utc),
        decision_impacts=decision_impacts,
    )



# =============================================================================
# Gemini Explanation Layer (Optional Enhancement)
# =============================================================================

EXPLANATION_TEMPLATE = """
Based on this week's security metrics:
- Risk Score: {score} ({trend})
- Key Changes: {changes}
- Priority Actions: {actions}

{ai_exposure}
"""


def fallback_explanation(brief: WeeklyBriefResponse) -> str:
    """Generate fallback explanation without Gemini."""
    trend = "improved" if brief.top_changes else "stable"
    changes = ", ".join(brief.top_changes[:3]) if brief.top_changes else "No major changes"
    actions = ", ".join([a.title for a in brief.top_3_actions]) if brief.top_3_actions else "No urgent actions"
    
    return EXPLANATION_TEMPLATE.format(
        score="Unknown",  # We don't have score in brief, this is template only
        trend=trend,
        changes=changes,
        actions=actions,
        ai_exposure=brief.ai_exposure_summary,
    ).strip()


async def enhance_with_gemini(brief: WeeklyBriefResponse) -> WeeklyBriefResponse:
    """
    Optionally enhance brief with Gemini-generated plain English explanation.
    
    AI GUARDRAILS:
    - Gemini only rewrites existing content
    - Has fallback if Gemini unavailable
    - Never blocks API response
    - Output is clamped to max length
    """
    if not settings.gemini_api_key:
        brief.explanation = fallback_explanation(brief)
        return brief
    
    try:
        import httpx
        
        # Build evidence payload for Gemini
        evidence = {
            "headline": brief.headline,
            "top_changes": brief.top_changes[:5],
            "top_actions": [a.title for a in brief.top_3_actions],
            "ai_exposure": brief.ai_exposure_summary,
            "confidence": brief.confidence_level,
        }
        
        prompt = (
            "SYSTEM: You are a security analyst. Rewrite this security brief into a 2-3 sentence "
            "executive summary that a non-technical executive can understand. Be concise and actionable.\n"
            f"USER: {evidence}"
        )
        
        params = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 150,
            },
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3:generateContent?key={settings.gemini_api_key}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=params)
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    # Clamp to reasonable length
                    words = text.split()
                    if len(words) > 100:
                        text = " ".join(words[:100]) + "..."
                    brief.explanation = text.strip()
                    return brief
        
        # Fallback if Gemini fails
        brief.explanation = fallback_explanation(brief)
        return brief
        
    except Exception:
        # Never let Gemini failures block the API
        brief.explanation = fallback_explanation(brief)
        return brief
