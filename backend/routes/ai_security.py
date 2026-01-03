"""
AI Security Routes (Phase 3)

Dedicated AI security monitoring endpoints:
- GET /api/v1/org/{org_id}/ai-security - Get comprehensive AI security posture

This provides a dedicated view of AI-related security concerns:
- Detected AI tools across all scans
- Exposed API key timeline
- Agent framework detection
- AI risk trend over time
- Plain-English explanations
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Organization, Scan, ScanAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org", tags=["ai-security"])


# =============================================================================
# Schemas
# =============================================================================

class AIToolDetected(BaseModel):
    """Detected AI tool information."""
    name: str = Field(..., description="Tool or library name")
    count: int = Field(1, ge=1, description="Number of times detected")
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_agent_framework: bool = Field(False, description="Whether this is an agent framework")


class ExposedKeyEvent(BaseModel):
    """Single key exposure event."""
    date: str = Field(..., description="Date YYYY-MM-DD")
    count: int = Field(..., ge=0, description="Number of keys exposed")
    key_types: List[str] = Field(default_factory=list, description="Types of keys exposed")


class AIRiskPoint(BaseModel):
    """Single point in AI risk timeline."""
    week_start: str = Field(..., description="Week start date YYYY-MM-DD")
    ai_score: int = Field(0, ge=0, le=100, description="AI risk score")
    delta: Optional[int] = Field(None, description="Change from previous week")


class AISecurityResponse(BaseModel):
    """
    Comprehensive AI security posture response.
    """
    org_id: str
    
    # Current posture
    ai_score: int = Field(0, ge=0, le=100, description="Current AI risk score")
    status: str = Field("clean", description="Status: clean, warning, critical")
    
    # Tools detected
    ai_tools_detected: List[AIToolDetected] = Field(default_factory=list)
    agent_frameworks: List[str] = Field(default_factory=list, description="Detected agent frameworks")
    
    # Key exposure
    exposed_keys_count: int = Field(0, ge=0, description="Current exposed key count")
    exposed_keys_timeline: List[ExposedKeyEvent] = Field(default_factory=list)
    
    # Trends
    ai_risk_trend: List[AIRiskPoint] = Field(default_factory=list)
    
    # Explanations
    explanation: str = Field("", description="Plain-English AI exposure summary")
    next_action: str = Field("", description="Recommended next action")
    
    # Metadata
    last_updated: Optional[datetime] = None


# =============================================================================
# Helpers
# =============================================================================

AGENT_KEYWORDS = ['langchain', 'crewai', 'autogen', 'langgraph', 'agent', 'openai-agents', 'llamaindex']

def is_agent_framework(tool_name: str) -> bool:
    """Check if a tool name indicates an agent framework."""
    lower_name = tool_name.lower()
    return any(kw in lower_name for kw in AGENT_KEYWORDS)


def get_ai_status(score: int) -> str:
    """Determine status based on AI score."""
    if score <= 20:
        return "clean"
    elif score <= 50:
        return "warning"
    else:
        return "critical"


def generate_ai_explanation(
    ai_score: int,
    tools_count: int,
    agent_count: int,
    keys_count: int,
    status: str
) -> str:
    """
    Generate plain-English explanation of AI exposure.
    Deterministic logic - no LLM.
    """
    if status == "clean" and tools_count == 0:
        return "No AI tools or frameworks detected in your organization's codebase. Your AI exposure is minimal."
    
    parts = []
    
    if keys_count > 0:
        parts.append(f"Found {keys_count} exposed AI API key{'s' if keys_count > 1 else ''}")
    
    if agent_count > 0:
        parts.append(f"detected {agent_count} agent framework{'s' if agent_count > 1 else ''}")
    
    if tools_count > 0:
        parts.append(f"{tools_count} AI tool{'s' if tools_count > 1 else ''} in use")
    
    explanation = "Your organization " + ", ".join(parts) + "."
    
    if status == "critical":
        explanation += " Immediate action required to secure exposed credentials."
    elif status == "warning":
        explanation += " Review your AI tooling for potential security gaps."
    
    return explanation


def determine_ai_next_action(
    status: str,
    keys_count: int,
    agent_count: int,
    tools_count: int
) -> str:
    """Determine next action for AI security. Deterministic logic."""
    if keys_count > 0:
        return "Rotate exposed AI API keys immediately and revoke old credentials"
    
    if status == "critical":
        return "Review agent framework access controls and implement proper sandboxing"
    
    if agent_count > 0:
        return "Audit agent framework configurations for proper access restrictions"
    
    if tools_count > 0:
        return "Maintain an inventory of approved AI tools and review data handling policies"
    
    return "Continue monitoring for new AI tool usage in your codebase"


# =============================================================================
# Endpoint
# =============================================================================

@router.get("/{org_id}/ai-security", response_model=AISecurityResponse)
async def get_ai_security(
    org_id: str,
    weeks: int = 12,
    db: Session = Depends(get_db),
):
    """
    Get comprehensive AI security posture for an organization.
    
    Returns:
    - Current AI risk score and status
    - All detected AI tools with usage counts
    - Agent framework detection
    - Exposed key timeline
    - AI risk trend over time
    - Plain-English explanations
    - Recommended next action
    
    This endpoint uses deterministic logic only. No LLM calls.
    """
    # Validate org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    weeks = min(max(weeks, 4), 52)
    start_date = now - timedelta(weeks=weeks)
    
    # Get all scans with AI data
    scans_with_ai = db.query(Scan).join(
        ScanAI, Scan.id == ScanAI.scan_id
    ).filter(
        Scan.org_id == org_id,
        Scan.created_at >= start_date
    ).order_by(Scan.created_at).all()
    
    # Aggregate AI tools across all scans
    tool_info = defaultdict(lambda: {
        'count': 0,
        'first_seen': None,
        'last_seen': None
    })
    
    # Aggregate exposed keys by date
    keys_by_date = defaultdict(lambda: {'count': 0, 'types': set()})
    
    # Track AI scores by week
    weekly_scores = defaultdict(list)
    
    # Current state from latest scan
    current_ai_score = 0
    current_keys_count = 0
    
    for scan in scans_with_ai:
        scan_ai = scan.scan_ai
        if not scan_ai:
            continue
        
        scan_date = scan.created_at
        if scan_date.tzinfo is None:
            scan_date = scan_date.replace(tzinfo=timezone.utc)
        
        # Week aggregation
        week_start = (scan_date - timedelta(days=scan_date.weekday())).date()
        weekly_scores[week_start].append(scan_ai.ai_score or 0)
        
        # Tool aggregation
        for tool in (scan_ai.ai_tools or []):
            tool_lower = tool.lower().strip()
            if tool_lower:
                tool_info[tool_lower]['count'] += 1
                if tool_info[tool_lower]['first_seen'] is None:
                    tool_info[tool_lower]['first_seen'] = scan_date
                tool_info[tool_lower]['last_seen'] = scan_date
        
        # Key exposure aggregation
        keys = scan_ai.ai_keys or []
        if keys:
            date_key = scan_date.date().isoformat()
            keys_by_date[date_key]['count'] += len(keys)
            for k in keys:
                if isinstance(k, dict) and 'key_type' in k:
                    keys_by_date[date_key]['types'].add(k['key_type'])
    
    # Get current state from latest scan
    latest_scan = scans_with_ai[-1] if scans_with_ai else None
    if latest_scan and latest_scan.scan_ai:
        current_ai_score = latest_scan.scan_ai.ai_score or 0
        current_keys_count = len(latest_scan.scan_ai.ai_keys or [])
    
    # Build tool list
    ai_tools_detected = []
    agent_frameworks = []
    
    for tool_name, info in tool_info.items():
        is_agent = is_agent_framework(tool_name)
        ai_tools_detected.append(AIToolDetected(
            name=tool_name,
            count=info['count'],
            first_seen=info['first_seen'],
            last_seen=info['last_seen'],
            is_agent_framework=is_agent
        ))
        if is_agent:
            agent_frameworks.append(tool_name)
    
    # Sort tools by count descending
    ai_tools_detected.sort(key=lambda x: x.count, reverse=True)
    
    # Build keys timeline
    exposed_keys_timeline = []
    for date_str in sorted(keys_by_date.keys()):
        data = keys_by_date[date_str]
        exposed_keys_timeline.append(ExposedKeyEvent(
            date=date_str,
            count=data['count'],
            key_types=list(data['types'])
        ))
    
    # Build AI risk trend
    ai_risk_trend = []
    sorted_weeks = sorted(weekly_scores.keys())
    prev_score = None
    
    for week_start in sorted_weeks:
        scores = weekly_scores[week_start]
        max_score = max(scores) if scores else 0
        delta = (max_score - prev_score) if prev_score is not None else None
        prev_score = max_score
        
        ai_risk_trend.append(AIRiskPoint(
            week_start=week_start.isoformat(),
            ai_score=max_score,
            delta=delta
        ))
    
    # Determine status
    status = get_ai_status(current_ai_score)
    
    # Generate explanation
    explanation = generate_ai_explanation(
        ai_score=current_ai_score,
        tools_count=len(ai_tools_detected),
        agent_count=len(agent_frameworks),
        keys_count=current_keys_count,
        status=status
    )
    
    # Determine next action
    next_action = determine_ai_next_action(
        status=status,
        keys_count=current_keys_count,
        agent_count=len(agent_frameworks),
        tools_count=len(ai_tools_detected)
    )
    
    return AISecurityResponse(
        org_id=org_id,
        ai_score=current_ai_score,
        status=status,
        ai_tools_detected=ai_tools_detected,
        agent_frameworks=agent_frameworks,
        exposed_keys_count=current_keys_count,
        exposed_keys_timeline=exposed_keys_timeline,
        ai_risk_trend=ai_risk_trend,
        explanation=explanation,
        next_action=next_action,
        last_updated=latest_scan.created_at if latest_scan else None,
    )
