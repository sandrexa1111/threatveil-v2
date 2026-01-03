"""
Asset Mapper Service

Provides helper functions to get-or-create assets for different entity types.
Assets are org-scoped and deduplicated by (org_id, type, name).
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import Asset


def get_or_create_domain_asset(
    db: Session,
    org_id: str,
    domain: str,
    risk_tags: Optional[List[str]] = None,
    properties: Optional[dict] = None,
) -> Asset:
    """
    Get or create a domain asset.
    
    Args:
        db: Database session
        org_id: Organization ID
        domain: Domain name (e.g., "example.com")
        risk_tags: Optional risk classification tags
        properties: Optional additional metadata
        
    Returns:
        Asset instance (existing or newly created)
    """
    domain = domain.lower().strip()
    
    # Try to find existing asset
    asset = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.type == "domain",
        Asset.name == domain,
    ).first()
    
    if asset:
        # Update risk_tags and properties if provided
        if risk_tags:
            existing_tags = asset.risk_tags or []
            asset.risk_tags = list(set(existing_tags + risk_tags))
        if properties:
            existing_props = asset.properties or {}
            existing_props.update(properties)
            asset.properties = existing_props
        asset.updated_at = datetime.utcnow()
        return asset
    
    # Create new asset
    asset = Asset(
        id=str(uuid.uuid4()),
        org_id=org_id,
        type="domain",
        name=domain,
        properties=properties or {},
        risk_tags=risk_tags or ["internet_exposed"],
    )
    db.add(asset)
    db.flush()
    return asset


def get_or_create_repo_asset(
    db: Session,
    org_id: str,
    full_name: str,
    risk_tags: Optional[List[str]] = None,
    properties: Optional[dict] = None,
) -> Asset:
    """
    Get or create a repository asset.
    
    Args:
        db: Database session
        org_id: Organization ID
        full_name: Repository full name (e.g., "org/repo")
        risk_tags: Optional risk classification tags
        properties: Optional additional metadata
        
    Returns:
        Asset instance (existing or newly created)
    """
    full_name = full_name.lower().strip()
    
    # Try to find existing asset
    asset = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.type == "repository",
        Asset.name == full_name,
    ).first()
    
    if asset:
        if risk_tags:
            existing_tags = asset.risk_tags or []
            asset.risk_tags = list(set(existing_tags + risk_tags))
        if properties:
            existing_props = asset.properties or {}
            existing_props.update(properties)
            asset.properties = existing_props
        asset.updated_at = datetime.utcnow()
        return asset
    
    # Create new asset
    asset = Asset(
        id=str(uuid.uuid4()),
        org_id=org_id,
        type="repository",
        name=full_name,
        properties=properties or {},
        risk_tags=risk_tags or [],
    )
    db.add(asset)
    db.flush()
    return asset


def get_or_create_ai_agent_asset(
    db: Session,
    org_id: str,
    agent_name: str,
    agent_type: str = "unknown",
    risk_tags: Optional[List[str]] = None,
    properties: Optional[dict] = None,
) -> Asset:
    """
    Get or create an AI agent asset.
    
    Args:
        db: Database session
        org_id: Organization ID
        agent_name: Agent identifier/name
        agent_type: Type of AI agent (e.g., "langchain", "crewai")
        risk_tags: Optional risk classification tags
        properties: Optional additional metadata
        
    Returns:
        Asset instance (existing or newly created)
    """
    agent_name = agent_name.lower().strip()
    
    # Try to find existing asset
    asset = db.query(Asset).filter(
        Asset.org_id == org_id,
        Asset.type == "ai_agent",
        Asset.name == agent_name,
    ).first()
    
    if asset:
        if risk_tags:
            existing_tags = asset.risk_tags or []
            asset.risk_tags = list(set(existing_tags + risk_tags))
        if properties:
            existing_props = asset.properties or {}
            existing_props.update(properties)
            asset.properties = existing_props
        asset.updated_at = datetime.utcnow()
        return asset
    
    # Create new asset
    props = properties or {}
    props["agent_type"] = agent_type
    
    asset = Asset(
        id=str(uuid.uuid4()),
        org_id=org_id,
        type="ai_agent",
        name=agent_name,
        properties=props,
        risk_tags=risk_tags or ["ai_exposure"],
    )
    db.add(asset)
    db.flush()
    return asset


def add_risk_tags_to_asset(
    db: Session,
    asset: Asset,
    tags: List[str],
) -> Asset:
    """
    Add risk tags to an existing asset.
    
    Args:
        db: Database session
        asset: Asset to update
        tags: Tags to add
        
    Returns:
        Updated asset
    """
    existing_tags = asset.risk_tags or []
    asset.risk_tags = list(set(existing_tags + tags))
    asset.updated_at = datetime.utcnow()
    db.flush()
    return asset
