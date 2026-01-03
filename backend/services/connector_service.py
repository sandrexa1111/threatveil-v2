"""
Connector Service - Phase 2.3 Low-Friction Internal Signals

Manages external service connectors with encrypted credentials.

Supported Connectors:
- github_app: GitHub organization inventory
- slack: Webhook delivery for weekly briefs

Security:
- Credentials encrypted at rest using Fernet symmetric encryption
- Credentials never exposed via API responses
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from ..models import Connector, Asset, Organization
from ..config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Encryption
# =============================================================================

def _get_fernet() -> Optional[Fernet]:
    """Get Fernet instance for credential encryption."""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a key for development (not recommended for production)
        logger.warning("ENCRYPTION_KEY not set - using derived key from JWT_SECRET")
        # Derive a Fernet-compatible key from JWT secret
        import hashlib
        import base64
        derived = hashlib.sha256(settings.jwt_secret.encode()).digest()
        key = base64.urlsafe_b64encode(derived)
    else:
        key = key.encode() if isinstance(key, str) else key
    
    try:
        return Fernet(key)
    except Exception as e:
        logger.error(f"Failed to initialize Fernet: {e}")
        return None


def encrypt_credentials(credentials: Dict[str, str]) -> Optional[str]:
    """Encrypt credentials dictionary to string."""
    fernet = _get_fernet()
    if not fernet:
        return None
    
    try:
        json_bytes = json.dumps(credentials).encode()
        encrypted = fernet.encrypt(json_bytes)
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None


def decrypt_credentials(encrypted: str) -> Optional[Dict[str, str]]:
    """Decrypt credentials string back to dictionary."""
    fernet = _get_fernet()
    if not fernet:
        return None
    
    try:
        decrypted = fernet.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())
    except InvalidToken:
        logger.error("Invalid encryption token - credentials corrupted or key changed")
        return None
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None


# =============================================================================
# Connector CRUD
# =============================================================================

def create_connector(
    db: Session,
    org_id: str,
    provider: str,
    credentials: Dict[str, str],
    name: Optional[str] = None,
    config: Dict[str, Any] = None,
    scopes: List[str] = None
) -> Tuple[Optional[Connector], Optional[str]]:
    """
    Create a new connector with encrypted credentials.
    
    Returns: (connector, error_message)
    """
    # Check organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None, "Organization not found"
    
    # Check for existing connector of same type
    existing = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.provider == provider
    ).first()
    
    if existing:
        return None, f"Connector of type {provider} already exists for this organization"
    
    # Encrypt credentials
    encrypted = encrypt_credentials(credentials)
    if encrypted is None:
        return None, "Failed to encrypt credentials"
    
    # Create connector
    connector = Connector(
        org_id=org_id,
        provider=provider,
        name=name or f"{provider.replace('_', ' ').title()} Connector",
        encrypted_credentials=encrypted,
        config=config or {},
        scopes=scopes or [],
        status='active'
    )
    
    db.add(connector)
    db.commit()
    db.refresh(connector)
    
    logger.info(f"Created {provider} connector for org {org_id}")
    return connector, None


def get_connector(
    db: Session,
    connector_id: str
) -> Optional[Connector]:
    """Get connector by ID."""
    return db.query(Connector).filter(Connector.id == connector_id).first()


def list_connectors(
    db: Session,
    org_id: str
) -> List[Connector]:
    """List all connectors for an organization."""
    return db.query(Connector).filter(
        Connector.org_id == org_id
    ).order_by(Connector.created_at.desc()).all()


def update_connector(
    db: Session,
    connector_id: str,
    updates: Dict[str, Any]
) -> Tuple[Optional[Connector], Optional[str]]:
    """Update connector configuration."""
    connector = db.query(Connector).filter(Connector.id == connector_id).first()
    if not connector:
        return None, "Connector not found"
    
    # Update allowed fields
    if 'name' in updates:
        connector.name = updates['name']
    if 'config' in updates:
        connector.config = updates['config']
    if 'status' in updates:
        connector.status = updates['status']
    
    connector.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(connector)
    
    return connector, None


def delete_connector(
    db: Session,
    connector_id: str
) -> Tuple[bool, Optional[str]]:
    """Delete a connector."""
    connector = db.query(Connector).filter(Connector.id == connector_id).first()
    if not connector:
        return False, "Connector not found"
    
    db.delete(connector)
    db.commit()
    
    return True, None


# =============================================================================
# Connector Sync Operations
# =============================================================================

async def sync_github_connector(
    db: Session,
    connector: Connector
) -> Dict[str, Any]:
    """
    Sync GitHub connector - fetches org repository inventory.
    
    Returns sync results with created assets.
    """
    import httpx
    
    # Decrypt credentials
    creds = decrypt_credentials(connector.encrypted_credentials)
    if not creds:
        connector.status = 'error'
        connector.last_error = "Failed to decrypt credentials"
        db.commit()
        return {"error": "Credential decryption failed"}
    
    token = creds.get('token') or creds.get('github_token')
    if not token:
        connector.status = 'error'
        connector.last_error = "No token in credentials"
        db.commit()
        return {"error": "No token found"}
    
    # Get org name from config
    github_org = connector.config.get('github_org')
    if not github_org:
        return {"error": "No github_org in config"}
    
    results = {
        "repos_synced": 0,
        "assets_created": 0,
        "signals_created": 0,
        "errors": []
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch repositories
            response = await client.get(
                f"https://api.github.com/orgs/{github_org}/repos",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json"
                },
                params={"per_page": 100, "sort": "updated"}
            )
            
            if response.status_code != 200:
                connector.status = 'error'
                connector.last_error = f"GitHub API error: {response.status_code}"
                db.commit()
                return {"error": f"GitHub API returned {response.status_code}"}
            
            repos = response.json()
            results["repos_synced"] = len(repos)
            
            # Create/update repository assets
            for repo in repos:
                existing = db.query(Asset).filter(
                    Asset.org_id == connector.org_id,
                    Asset.type == 'github_repo',
                    Asset.name == repo['full_name']
                ).first()
                
                if not existing:
                    asset = Asset(
                        org_id=connector.org_id,
                        type='github_repo',
                        name=repo['full_name'],
                        properties={
                            'private': repo.get('private', False),
                            'language': repo.get('language'),
                            'archived': repo.get('archived', False),
                            'default_branch': repo.get('default_branch'),
                            'topics': repo.get('topics', []),
                            'has_security_policy': repo.get('security', {}).get('security_policy', False)
                        }
                    )
                    db.add(asset)
                    results["assets_created"] += 1
        
        # Update connector status
        connector.status = 'active'
        connector.last_sync_at = datetime.now(timezone.utc)
        connector.last_error = None
        db.commit()
        
    except Exception as e:
        logger.error(f"GitHub sync failed: {e}")
        connector.status = 'error'
        connector.last_error = str(e)
        db.commit()
        results["errors"].append(str(e))
    
    return results


async def sync_connector(
    db: Session,
    connector: Connector
) -> Dict[str, Any]:
    """Dispatch sync to appropriate handler."""
    if connector.provider == 'github_app':
        return await sync_github_connector(db, connector)
    else:
        return {"error": f"Sync not implemented for {connector.provider}"}


async def sync_all_connectors(
    db: Session,
    org_id: str
) -> Dict[str, Any]:
    """Sync all active connectors for an organization."""
    connectors = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.status.in_(['active', 'error'])
    ).all()
    
    results = {
        "synced": [],
        "errors": []
    }
    
    for connector in connectors:
        try:
            sync_result = await sync_connector(db, connector)
            if "error" in sync_result:
                results["errors"].append({
                    "connector_id": connector.id,
                    "error": sync_result["error"]
                })
            else:
                results["synced"].append({
                    "connector_id": connector.id,
                    "provider": connector.provider,
                    **sync_result
                })
        except Exception as e:
            results["errors"].append({
                "connector_id": connector.id,
                "error": str(e)
            })
    
    return results
