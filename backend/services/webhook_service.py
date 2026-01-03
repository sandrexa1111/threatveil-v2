"""
Webhook Service - Phase 2.3 Automation Hooks

Manages webhook configuration and delivery with HMAC signing.

Event Types:
- weekly_brief.generated: Weekly brief is ready
- decision.created: New security decision generated
- decision.verified: Decision fix has been verified
- risk.score_changed: Organization risk score changed significantly
"""
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from ..models import Webhook, WebhookDelivery, Organization

logger = logging.getLogger(__name__)


# =============================================================================
# Webhook CRUD
# =============================================================================

def create_webhook(
    db: Session,
    org_id: str,
    url: str,
    events: List[str],
    name: Optional[str] = None,
    headers: Dict[str, str] = None,
    enabled: bool = True
) -> Tuple[Optional[Webhook], Optional[str]]:
    """
    Create a new webhook with auto-generated secret.
    
    Returns: (webhook, error_message)
    """
    # Validate org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None, "Organization not found"
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return None, "Webhook URL must start with http:// or https://"
    
    # Validate events
    valid_events = ['weekly_brief.generated', 'decision.created', 'decision.verified', 'risk.score_changed']
    invalid = [e for e in events if e not in valid_events]
    if invalid:
        return None, f"Invalid event types: {invalid}"
    
    # Generate signing secret
    secret = secrets.token_hex(32)
    
    webhook = Webhook(
        org_id=org_id,
        name=name,
        url=url,
        secret=secret,
        events=events,
        headers=headers or {},
        enabled=enabled
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    logger.info(f"Created webhook {webhook.id} for org {org_id}")
    return webhook, None


def get_webhook(db: Session, webhook_id: str) -> Optional[Webhook]:
    """Get webhook by ID."""
    return db.query(Webhook).filter(Webhook.id == webhook_id).first()


def list_webhooks(db: Session, org_id: str) -> List[Webhook]:
    """List all webhooks for an organization."""
    return db.query(Webhook).filter(
        Webhook.org_id == org_id
    ).order_by(Webhook.created_at.desc()).all()


def update_webhook(
    db: Session,
    webhook_id: str,
    updates: Dict[str, Any]
) -> Tuple[Optional[Webhook], Optional[str]]:
    """Update webhook configuration."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        return None, "Webhook not found"
    
    if 'name' in updates:
        webhook.name = updates['name']
    if 'url' in updates:
        webhook.url = updates['url']
    if 'events' in updates:
        webhook.events = updates['events']
    if 'headers' in updates:
        webhook.headers = updates['headers']
    if 'enabled' in updates:
        webhook.enabled = updates['enabled']
    
    webhook.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(webhook)
    
    return webhook, None


def delete_webhook(db: Session, webhook_id: str) -> Tuple[bool, Optional[str]]:
    """Delete a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        return False, "Webhook not found"
    
    db.delete(webhook)
    db.commit()
    return True, None


# =============================================================================
# Webhook Signing
# =============================================================================

def compute_hmac_signature(payload: bytes, secret: str) -> str:
    """
    Compute HMAC-SHA256 signature for webhook payload.
    
    The signature is returned as a hex-encoded string with 'sha256=' prefix.
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_signature(payload: bytes, secret: str, signature: str) -> bool:
    """Verify HMAC signature."""
    computed = compute_hmac_signature(payload, secret)
    return hmac.compare_digest(computed, signature)


# =============================================================================
# Webhook Delivery
# =============================================================================

async def deliver_webhook(
    db: Session,
    webhook: Webhook,
    event_type: str,
    payload: Dict[str, Any],
    max_retries: int = 3
) -> WebhookDelivery:
    """
    Deliver a webhook with retry logic.
    
    Returns the WebhookDelivery record.
    """
    # Create delivery record
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=payload,
        status='pending',
        max_attempts=max_retries
    )
    db.add(delivery)
    db.commit()
    
    # Prepare payload
    event_payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload
    }
    payload_bytes = json.dumps(event_payload, default=str).encode('utf-8')
    
    # Compute signature
    signature = compute_hmac_signature(payload_bytes, webhook.secret)
    
    # Build headers
    headers = {
        "Content-Type": "application/json",
        "X-ThreatVeil-Event": event_type,
        "X-ThreatVeil-Signature": signature,
        "X-ThreatVeil-Delivery": delivery.id,
        "User-Agent": "ThreatVeil-Webhook/1.0"
    }
    headers.update(webhook.headers or {})
    
    # Attempt delivery with retries
    last_error = None
    for attempt in range(1, max_retries + 1):
        delivery.attempts = attempt
        delivery.last_attempt_at = datetime.now(timezone.utc)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_bytes,
                    headers=headers
                )
                
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000]  # Limit stored body
                
                if 200 <= response.status_code < 300:
                    delivery.status = 'success'
                    delivery.completed_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(f"Webhook {webhook.id} delivered successfully: {event_type}")
                    return delivery
                else:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(f"Webhook delivery failed with {response.status_code}")
        
        except httpx.TimeoutException:
            last_error = "Request timeout"
            logger.warning(f"Webhook delivery timed out (attempt {attempt})")
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"Webhook delivery error: {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries:
            import asyncio
            await asyncio.sleep(2 ** attempt)
    
    # All retries failed
    delivery.status = 'failed'
    delivery.error = last_error
    delivery.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.error(f"Webhook {webhook.id} delivery failed after {max_retries} attempts: {last_error}")
    return delivery


async def emit_event(
    db: Session,
    org_id: str,
    event_type: str,
    payload: Dict[str, Any]
) -> List[WebhookDelivery]:
    """
    Emit an event to all subscribed webhooks for an organization.
    
    Returns list of delivery records.
    """
    # Find all enabled webhooks subscribed to this event
    webhooks = db.query(Webhook).filter(
        Webhook.org_id == org_id,
        Webhook.enabled == True
    ).all()
    
    deliveries = []
    for webhook in webhooks:
        if event_type in webhook.events:
            try:
                delivery = await deliver_webhook(db, webhook, event_type, payload)
                deliveries.append(delivery)
            except Exception as e:
                logger.error(f"Failed to deliver to webhook {webhook.id}: {e}")
    
    return deliveries


# =============================================================================
# Webhook Testing
# =============================================================================

async def test_webhook(
    db: Session,
    webhook: Webhook
) -> Dict[str, Any]:
    """
    Send a test event to a webhook.
    """
    test_payload = {
        "message": "This is a test webhook from ThreatVeil",
        "webhook_id": webhook.id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        delivery = await deliver_webhook(
            db, webhook, 
            event_type="test",
            payload=test_payload,
            max_retries=1
        )
        
        return {
            "success": delivery.status == 'success',
            "status_code": delivery.response_code,
            "message": "Test webhook delivered successfully" if delivery.status == 'success' else f"Failed: {delivery.error}"
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Error: {str(e)}"
        }


# =============================================================================
# n8n Template Generation
# =============================================================================

def generate_n8n_template(
    org_id: str,
    webhook_url: str = "{{YOUR_N8N_WEBHOOK_URL}}"
) -> Dict[str, Any]:
    """
    Generate an n8n workflow template for ThreatVeil integration.
    """
    return {
        "name": "ThreatVeil Security Alerts",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "threatveil-webhook",
                    "authentication": "headerAuth"
                },
                "id": "webhook",
                "name": "ThreatVeil Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "conditions": {
                        "options": {
                            "caseSensitive": True
                        },
                        "conditions": [
                            {
                                "id": "eq1",
                                "leftValue": "={{ $json.event }}",
                                "rightValue": "decision.created",
                                "operator": {
                                    "type": "string",
                                    "operation": "equals"
                                }
                            }
                        ]
                    }
                },
                "id": "if-decision",
                "name": "Is Decision?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "channel": "#security-alerts",
                    "text": "=🔒 New Security Decision: {{ $json.data.title }}\n\nPriority: {{ $json.data.priority }}\nEffort: {{ $json.data.effort_estimate }}\nRisk Reduction: {{ $json.data.estimated_risk_reduction }}%"
                },
                "id": "slack",
                "name": "Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 1,
                "position": [650, 200]
            }
        ],
        "connections": {
            "ThreatVeil Webhook": {
                "main": [
                    [{"node": "Is Decision?", "type": "main", "index": 0}]
                ]
            },
            "Is Decision?": {
                "main": [
                    [{"node": "Slack", "type": "main", "index": 0}],
                    []
                ]
            }
        },
        "active": False,
        "settings": {
            "executionOrder": "v1"
        },
        "versionId": "1"
    }
