"""
AI Governance Routes - Phase 2.3

Provides endpoints for AI governance dashboard:
- GET /api/v1/org/{org_id}/ai-governance - AI posture overview
- GET /api/v1/org/{org_id}/ai-assets - AI asset inventory
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Organization, AIAsset
from ..schemas import (
    AIGovernanceResponse,
    AIAssetRead,
    AIAssetListResponse,
    DecisionSummary
)
from ..services.ai_assets_service import (
    get_ai_governance_summary,
    get_ai_assets_list,
    calculate_ai_posture_score
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org", tags=["ai-governance"])


# =============================================================================
# AI Governance Dashboard
# =============================================================================

@router.get("/{org_id}/ai-governance", response_model=AIGovernanceResponse)
async def get_ai_governance(
    org_id: str,
    db: Session = Depends(get_db)
):
    """
    Get AI Governance overview for the organization.
    
    Returns:
        - ai_posture_score: 0-100 score (higher is better)
        - ai_posture_status: clean | warning | critical
        - ai_posture_trend: score change from last period
        - assets_by_type: count of AI assets by type
        - total_ai_assets: total count
        - top_ai_risks: top 5 AI-related signals
        - ai_decisions_this_week: decisions related to AI
    """
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        summary = get_ai_governance_summary(db, org_id)
        
        return AIGovernanceResponse(
            ai_posture_score=summary['ai_posture_score'],
            ai_posture_status=summary['ai_posture_status'],
            ai_posture_trend=summary['ai_posture_trend'],
            assets_by_type=summary['assets_by_type'],
            total_ai_assets=summary['total_ai_assets'],
            top_ai_risks=[],  # Simplified for now - TODO: add signal serialization
            ai_decisions_this_week=[
                DecisionSummary(
                    id=d.id,
                    title=d.title,
                    effort_estimate=d.effort_estimate,
                    estimated_risk_reduction=d.estimated_risk_reduction,
                    priority=d.priority,
                    status=d.status,
                    business_impact=d.business_impact,
                    confidence_score=d.confidence_score,
                    asset_name=None
                ) for d in summary['ai_decisions_this_week']
            ],
            last_updated=summary.get('last_updated')
        )
    except Exception as e:
        logger.error(f"Error fetching AI governance for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch AI governance data: {str(e)}"
        )


@router.get("/{org_id}/ai-assets", response_model=AIAssetListResponse)
async def list_ai_assets(
    org_id: str,
    asset_type: Optional[str] = Query(None, description="Filter by type: model_provider, agent_framework, vector_db, etc."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of AI assets for the organization.
    
    Supports filtering by asset type:
    - model_provider: OpenAI, Anthropic, Google, etc.
    - agent_framework: LangChain, CrewAI, AutoGen
    - vector_db: Pinecone, Weaviate, Chroma
    - prompt_repo: Prompt templates and configs
    - automation_tool: n8n/Zapier AI integrations
    - dataset: Training data files
    """
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    assets, total = get_ai_assets_list(
        db, org_id,
        asset_type=asset_type,
        page=page,
        page_size=page_size
    )
    
    return AIAssetListResponse(
        assets=[
            AIAssetRead(
                id=a.id,
                org_id=a.org_id,
                type=a.type,
                name=a.name,
                evidence=a.evidence or {},
                risk_tags=a.risk_tags or [],
                source=a.source,
                repository=a.repository,
                file_path=a.file_path,
                first_seen_at=a.first_seen_at,
                last_seen_at=a.last_seen_at,
                status=a.status
            ) for a in assets
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )


@router.get("/{org_id}/ai-posture")
async def get_ai_posture_score(
    org_id: str,
    db: Session = Depends(get_db)
):
    """
    Get just the AI posture score (lightweight endpoint for widgets).
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    score, status, trend = calculate_ai_posture_score(db, org_id)
    
    return {
        "ai_posture_score": score,
        "ai_posture_status": status,
        "ai_posture_trend": trend
    }
