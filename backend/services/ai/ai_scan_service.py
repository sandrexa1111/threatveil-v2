"""AI scan service for ThreatVeil Horizon - orchestrates AI detection and ScanAI creation."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from ...models import Scan, ScanAI
from ..github_service import search_code_leaks
from .ai_scoring import compute_ai_score
from .ai_summary_service import generate_ai_summary, fallback_ai_summary
from .github_ai_service import scan_github_for_ai_indicators


async def ai_scan_for_scan(scan: Scan, db: Session) -> Optional[ScanAI]:
    """
    Perform AI-specific scanning for a Scan and create/update ScanAI record.
    
    This function:
    1. Runs AI-related detectors (GitHub AI + key checks)
    2. Computes ai_score using ai_scoring.compute_ai_score()
    3. Generates ai_summary using Gemini (with fallback)
    4. Creates and persists a ScanAI row linked to the Scan
    
    Args:
        scan: The Scan model instance
        db: Database session
    
    Returns:
        ScanAI instance if created successfully, None otherwise
    """
    try:
        # Extract GitHub org from scan
        github_org = scan.github_org or ""
        
        # Run GitHub AI indicator scan
        ai_indicators = await scan_github_for_ai_indicators(github_org)
        
        # Extract data
        ai_libraries_meta = ai_indicators.get("ai_libraries", [])
        ai_tools = list(set([lib.get("library", "") for lib in ai_libraries_meta if lib.get("library")]))
        
        ai_files = ai_indicators.get("ai_files", [])
        ai_agents = ai_indicators.get("ai_agents", [])
        ai_keys = ai_indicators.get("ai_keys", [])
        
        # Also check for AI key leaks via existing GitHub service
        # This provides additional coverage
        github_leaks, _ = await search_code_leaks(github_org)
        
        # Merge AI-specific key leaks with general leaks
        # Filter for AI-related keys
        ai_key_leaks = []
        for leak in github_leaks:
            path_lower = leak.get("path", "").lower()
            if any(keyword in path_lower for keyword in ["openai", "gemini", "anthropic", "huggingface", "cohere"]):
                ai_key_leaks.append({
                    "key_type": "ai_key",
                    "repository": leak.get("repository"),
                    "path": leak.get("path"),
                    "url": leak.get("html_url"),
                })
        
        # Combine with AI-specific key detections
        all_ai_keys = ai_keys + ai_key_leaks
        
        # Compute AI score
        ai_score = compute_ai_score(
            ai_tools=ai_tools,
            ai_vendors=[],  # Empty for now, to be implemented in Horizon vendor phase
            ai_keys=all_ai_keys,
        )
        
        # Get organization info for summary (use org instead of company)
        org = getattr(scan, 'organization', None)
        company_name = getattr(org, 'name', None) if org else None
        domain = scan.domain
        
        # Generate AI summary
        ai_summary = await generate_ai_summary(
            ai_tools=ai_tools,
            ai_keys=all_ai_keys,
            ai_score=ai_score,
            domain=domain,
            company_name=company_name,
        )
        
        # Check if ScanAI already exists for this scan
        existing_scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan.id).first()
        
        if existing_scan_ai:
            # Update existing record
            existing_scan_ai.ai_tools = ai_tools
            existing_scan_ai.ai_vendors = []  # Empty for now
            existing_scan_ai.ai_keys = all_ai_keys
            existing_scan_ai.ai_score = ai_score
            existing_scan_ai.ai_summary = ai_summary
            db.flush()
            return existing_scan_ai
        else:
            # Create new ScanAI record
            scan_ai = ScanAI(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                ai_tools=ai_tools,
                ai_vendors=[],  # Empty for now
                ai_keys=all_ai_keys,
                ai_score=ai_score,
                ai_summary=ai_summary,
            )
            db.add(scan_ai)
            db.flush()
            return scan_ai
    
    except Exception as e:
        # Log error but don't crash the scan flow
        # Create a minimal ScanAI entry with fallback data
        try:
            # Ensure we have at least a basic ScanAI entry
            existing_scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan.id).first()
            if existing_scan_ai:
                return existing_scan_ai
            
            # Create minimal entry with fallback summary
            org = getattr(scan, 'organization', None)
            fallback_summary_text = fallback_ai_summary(
                ai_tools=[],
                ai_keys=[],
                domain=scan.domain,
                company_name=getattr(org, 'name', None) if org else None,
            )
            
            scan_ai = ScanAI(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                ai_tools=[],
                ai_vendors=[],
                ai_keys=[],
                ai_score=0,
                ai_summary=fallback_summary_text,
            )
            db.add(scan_ai)
            db.flush()
            return scan_ai
        except Exception:
            # If even fallback fails, return None (scan will still succeed)
            return None


