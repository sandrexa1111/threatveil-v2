"""
Webhook Routes - Phase 2.3 Automation Hooks

Provides endpoints for webhook management:
- POST /api/v1/org/{org_id}/webhooks - Create webhook
- GET /api/v1/org/{org_id}/webhooks - List webhooks
- POST /api/v1/org/{org_id}/webhooks/test - Test webhook
- GET /api/v1/org/{org_id}/integrations/n8n-template - Get n8n template
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Organization, Webhook
from ..schemas import (
    WebhookCreate,
    WebhookRead,
    WebhookListResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    N8nTemplateResponse
)
from ..services.webhook_service import (
    create_webhook,
    list_webhooks,
    get_webhook,
    update_webhook,
    delete_webhook,
    test_webhook,
    generate_n8n_template
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org", tags=["webhooks"])


# =============================================================================
# Webhook CRUD
# =============================================================================

@router.post("/{org_id}/webhooks", response_model=WebhookRead)
async def create_new_webhook(
    org_id: str,
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new webhook for an organization.
    
    Supported events:
    - weekly_brief.generated
    - decision.created
    - decision.verified
    - risk.score_changed
    
    A signing secret is auto-generated. Include X-ThreatVeil-Signature header 
    validation in your webhook receiver.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    webhook, error = create_webhook(
        db=db,
        org_id=org_id,
        url=webhook_data.url,
        events=webhook_data.events,
        name=webhook_data.name,
        headers=webhook_data.headers,
        enabled=webhook_data.enabled
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return WebhookRead(
        id=webhook.id,
        org_id=webhook.org_id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events,
        headers=webhook.headers,
        enabled=webhook.enabled,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at
    )


@router.get("/{org_id}/webhooks", response_model=WebhookListResponse)
async def list_org_webhooks(
    org_id: str,
    db: Session = Depends(get_db)
):
    """
    List all webhooks for an organization.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    webhooks = list_webhooks(db, org_id)
    
    return WebhookListResponse(
        webhooks=[
            WebhookRead(
                id=w.id,
                org_id=w.org_id,
                name=w.name,
                url=w.url,
                events=w.events,
                headers=w.headers,
                enabled=w.enabled,
                created_at=w.created_at,
                updated_at=w.updated_at
            ) for w in webhooks
        ],
        total=len(webhooks)
    )


@router.get("/{org_id}/webhooks/{webhook_id}", response_model=WebhookRead)
async def get_webhook_details(
    org_id: str,
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific webhook."""
    webhook = get_webhook(db, webhook_id)
    if not webhook or webhook.org_id != org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookRead(
        id=webhook.id,
        org_id=webhook.org_id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events,
        headers=webhook.headers,
        enabled=webhook.enabled,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at
    )


@router.delete("/{org_id}/webhooks/{webhook_id}")
async def delete_org_webhook(
    org_id: str,
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """Delete a webhook."""
    webhook = get_webhook(db, webhook_id)
    if not webhook or webhook.org_id != org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    success, error = delete_webhook(db, webhook_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Webhook deleted"}


# =============================================================================
# Webhook Testing
# =============================================================================

@router.post("/{org_id}/webhooks/test", response_model=WebhookTestResponse)
async def test_org_webhook(
    org_id: str,
    test_request: WebhookTestRequest,
    db: Session = Depends(get_db)
):
    """
    Send a test event to a webhook.
    
    This sends a "test" event type with sample data.
    """
    webhook = get_webhook(db, test_request.webhook_id)
    if not webhook or webhook.org_id != org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    result = await test_webhook(db, webhook)
    
    return WebhookTestResponse(
        success=result["success"],
        status_code=result.get("status_code"),
        message=result["message"]
    )


# =============================================================================
# Integration Templates
# =============================================================================

@router.get("/{org_id}/integrations/n8n-template", response_model=N8nTemplateResponse)
async def get_n8n_template(
    org_id: str,
    db: Session = Depends(get_db)
):
    """
    Get an n8n workflow template for ThreatVeil integration.
    
    The template includes:
    - Webhook trigger node
    - Conditional routing by event type
    - Slack notification node
    
    Import this template into n8n and customize as needed.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    template = generate_n8n_template(org_id)
    
    return N8nTemplateResponse(
        name=template["name"],
        workflow=template,
        description="ThreatVeil security alerts workflow for n8n. Import this template and configure your Slack credentials."
    )


@router.get("/{org_id}/webhooks/{webhook_id}/secret")
async def get_webhook_secret(
    org_id: str,
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the signing secret for a webhook.
    
    ⚠️ This endpoint should be called only once after creation.
    Store the secret securely in your webhook receiver.
    """
    webhook = get_webhook(db, webhook_id)
    if not webhook or webhook.org_id != org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {
        "webhook_id": webhook.id,
        "secret": webhook.secret,
        "message": "Store this secret securely. It won't be shown again."
    }
