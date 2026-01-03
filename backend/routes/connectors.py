"""
Connector Routes - Phase 2.3 Low-Friction Internal Signals

Provides endpoints for managing external service connectors:
- POST /api/v1/org/{org_id}/connectors - Create connector
- GET /api/v1/org/{org_id}/connectors - List connectors
- POST /api/v1/org/{org_id}/sync - Trigger sync
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Organization
from ..schemas import (
    ConnectorCreate,
    ConnectorRead,
    ConnectorListResponse,
    ConnectorSyncRequest,
    ConnectorSyncResponse
)
from ..services.connector_service import (
    create_connector,
    list_connectors,
    get_connector,
    sync_all_connectors,
    sync_connector
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org", tags=["connectors"])


# =============================================================================
# Connector Endpoints
# =============================================================================

@router.post("/{org_id}/connectors", response_model=ConnectorRead)
async def create_new_connector(
    org_id: str,
    connector_data: ConnectorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new connector for an organization.
    
    Supported providers:
    - github_app: GitHub organization inventory (requires token)
    - slack: Slack webhook for notifications (requires webhook_url)
    
    Credentials are encrypted at rest and never exposed via API.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    connector, error = create_connector(
        db=db,
        org_id=org_id,
        provider=connector_data.provider,
        credentials=connector_data.credentials,
        name=connector_data.name,
        config=connector_data.config,
        scopes=connector_data.scopes
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return ConnectorRead(
        id=connector.id,
        org_id=connector.org_id,
        provider=connector.provider,
        name=connector.name,
        status=connector.status,
        scopes=connector.scopes,
        config=connector.config,
        last_sync_at=connector.last_sync_at,
        last_error=connector.last_error,
        created_at=connector.created_at,
        updated_at=connector.updated_at
    )


@router.get("/{org_id}/connectors", response_model=ConnectorListResponse)
async def list_org_connectors(
    org_id: str,
    db: Session = Depends(get_db)
):
    """
    List all connectors for an organization.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    connectors = list_connectors(db, org_id)
    
    return ConnectorListResponse(
        connectors=[
            ConnectorRead(
                id=c.id,
                org_id=c.org_id,
                provider=c.provider,
                name=c.name,
                status=c.status,
                scopes=c.scopes,
                config=c.config,
                last_sync_at=c.last_sync_at,
                last_error=c.last_error,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in connectors
        ],
        total=len(connectors)
    )


@router.post("/{org_id}/sync", response_model=ConnectorSyncResponse)
async def sync_connectors(
    org_id: str,
    sync_request: Optional[ConnectorSyncRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Trigger sync for organization connectors.
    
    If connector_id is provided, syncs only that connector.
    Otherwise syncs all active connectors.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if sync_request and sync_request.connector_id:
        # Sync specific connector
        connector = get_connector(db, sync_request.connector_id)
        if not connector or connector.org_id != org_id:
            raise HTTPException(status_code=404, detail="Connector not found")
        
        result = await sync_connector(db, connector)
        
        if "error" in result:
            return ConnectorSyncResponse(
                synced_connectors=[],
                assets_created=0,
                signals_created=0,
                errors=[result["error"]]
            )
        
        return ConnectorSyncResponse(
            synced_connectors=[connector.id],
            assets_created=result.get("assets_created", 0),
            signals_created=result.get("signals_created", 0),
            errors=result.get("errors", [])
        )
    
    # Sync all connectors
    results = await sync_all_connectors(db, org_id)
    
    return ConnectorSyncResponse(
        synced_connectors=[s["connector_id"] for s in results["synced"]],
        assets_created=sum(s.get("assets_created", 0) for s in results["synced"]),
        signals_created=sum(s.get("signals_created", 0) for s in results["synced"]),
        errors=[e["error"] for e in results["errors"]]
    )


# =============================================================================
# GitHub-Specific Endpoints
# =============================================================================

@router.post("/{org_id}/connectors/github")
async def create_github_connector(
    org_id: str,
    token: str,
    github_org: str,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a GitHub connector (convenience endpoint).
    
    Args:
        token: GitHub personal access token or app token
        github_org: GitHub organization name to sync
        name: Optional display name
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    connector, error = create_connector(
        db=db,
        org_id=org_id,
        provider="github_app",
        credentials={"token": token},
        name=name or f"GitHub: {github_org}",
        config={"github_org": github_org},
        scopes=["repo:read", "org:read"]
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "id": connector.id,
        "provider": connector.provider,
        "status": connector.status,
        "message": f"GitHub connector created for {github_org}"
    }


# =============================================================================
# Slack-Specific Endpoints  
# =============================================================================

@router.post("/{org_id}/connectors/slack")
async def create_slack_connector(
    org_id: str,
    webhook_url: str,
    channel: str = "#security-alerts",
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a Slack connector (convenience endpoint).
    
    Args:
        webhook_url: Slack incoming webhook URL
        channel: Default channel for notifications
        name: Optional display name
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    connector, error = create_connector(
        db=db,
        org_id=org_id,
        provider="slack",
        credentials={"webhook_url": webhook_url},
        name=name or f"Slack: {channel}",
        config={"default_channel": channel},
        scopes=["incoming-webhook"]
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "id": connector.id,
        "provider": connector.provider,
        "status": connector.status,
        "message": f"Slack connector created for {channel}"
    }
