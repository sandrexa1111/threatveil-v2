"""
AI Assets Service - Phase 2.3 AI Governance

Manages AI asset inventory and computes AI posture score.

AI Asset Types:
- model_provider: OpenAI, Anthropic, Google, Cohere, HuggingFace
- agent_framework: LangChain, LangGraph, CrewAI, AutoGen
- prompt_repo: Prompt templates, AI config files
- vector_db: Pinecone, Weaviate, pgvector usage
- automation_tool: n8n/Zapier AI integrations, MCP servers
- dataset: Dataset files with potential PII
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import AIAsset, Organization, Scan, ScanAI, Signal, SecurityDecision

logger = logging.getLogger(__name__)


# =============================================================================
# AI Detection Patterns
# =============================================================================

AI_PROVIDERS = {
    'openai': ('OpenAI', ['openai', 'gpt-4', 'gpt-3.5', 'chatgpt', 'davinci']),
    'anthropic': ('Anthropic', ['anthropic', 'claude', 'claude-3']),
    'google': ('Google AI', ['gemini', 'palm', 'vertex', 'bard', 'google-generativeai']),
    'cohere': ('Cohere', ['cohere', 'command-r']),
    'huggingface': ('HuggingFace', ['huggingface', 'transformers', 'diffusers']),
    'mistral': ('Mistral', ['mistral', 'mixtral']),
    'replicate': ('Replicate', ['replicate']),
}

AI_FRAMEWORKS = {
    'langchain': ('LangChain', ['langchain', 'langchain-core']),
    'langgraph': ('LangGraph', ['langgraph']),
    'crewai': ('CrewAI', ['crewai', 'crew-ai']),
    'autogen': ('AutoGen', ['autogen', 'pyautogen']),
    'llamaindex': ('LlamaIndex', ['llama-index', 'llamaindex']),
    'haystack': ('Haystack', ['haystack', 'farm-haystack']),
    'dspy': ('DSPy', ['dspy', 'dsp-ml']),
    'semantic-kernel': ('Semantic Kernel', ['semantic-kernel']),
}

VECTOR_DBS = {
    'pinecone': ('Pinecone', ['pinecone', 'pinecone-client']),
    'weaviate': ('Weaviate', ['weaviate', 'weaviate-client']),
    'chromadb': ('ChromaDB', ['chromadb', 'chroma']),
    'qdrant': ('Qdrant', ['qdrant', 'qdrant-client']),
    'pgvector': ('pgvector', ['pgvector']),
    'milvus': ('Milvus', ['pymilvus', 'milvus']),
}

AUTOMATION_TOOLS = {
    'n8n': ('n8n', ['n8n', '@n8n/']),
    'zapier': ('Zapier', ['zapier']),
    'make': ('Make/Integromat', ['make', 'integromat']),
    'pipedream': ('Pipedream', ['pipedream']),
}

# Risky file patterns for AI governance
RISKY_AI_PATTERNS = {
    'prompt_files': ['.prompt', '.prompt.yaml', '.prompt.yml', 'prompts/', 'prompt_templates/'],
    'config_files': ['ai_config', 'llm_config', 'agent_config', 'mcp.json', 'tools.json'],
    'dataset_files': ['dataset', 'training_data', '.csv', '.jsonl'],
}


# =============================================================================
# AI Asset Detection
# =============================================================================

def detect_ai_assets_from_scan(
    org_id: str,
    scan: Scan,
    scan_ai: Optional[ScanAI],
    db: Session
) -> List[AIAsset]:
    """
    Detect AI assets from scan results and create/update records.
    
    Args:
        org_id: Organization ID
        scan: The completed scan
        scan_ai: AI-specific scan data (if available)
        db: Database session
        
    Returns:
        List of created/updated AIAsset records
    """
    assets_created = []
    now = datetime.now(timezone.utc)
    
    if not scan_ai:
        return assets_created
    
    # Process detected AI tools
    ai_tools = scan_ai.ai_tools or []
    for tool in ai_tools:
        tool_lower = tool.lower()
        
        # Check providers
        for key, (name, patterns) in AI_PROVIDERS.items():
            if any(p in tool_lower for p in patterns):
                asset = _get_or_create_ai_asset(
                    db, org_id, 'model_provider', name,
                    evidence={'detected_as': tool, 'source': 'github_scan'},
                    source='github'
                )
                assets_created.append(asset)
        
        # Check frameworks
        for key, (name, patterns) in AI_FRAMEWORKS.items():
            if any(p in tool_lower for p in patterns):
                asset = _get_or_create_ai_asset(
                    db, org_id, 'agent_framework', name,
                    evidence={'detected_as': tool, 'source': 'github_scan'},
                    source='github',
                    risk_tags=['agent_framework']
                )
                assets_created.append(asset)
        
        # Check vector DBs
        for key, (name, patterns) in VECTOR_DBS.items():
            if any(p in tool_lower for p in patterns):
                asset = _get_or_create_ai_asset(
                    db, org_id, 'vector_db', name,
                    evidence={'detected_as': tool, 'source': 'github_scan'},
                    source='github'
                )
                assets_created.append(asset)
    
    # Process AI key leaks - these are high-risk
    ai_keys = scan_ai.ai_keys or []
    for key_leak in ai_keys:
        key_type = key_leak.get('key_type', 'unknown')
        provider = key_type.replace('_KEY', '').replace('API_KEY', '').lower()
        
        asset = _get_or_create_ai_asset(
            db, org_id, 'model_provider', f"{provider.title()} (Leaked Key)",
            evidence={
                'key_type': key_type,
                'repository': key_leak.get('repository'),
                'path': key_leak.get('path'),
                'source': 'key_scan'
            },
            source='github',
            risk_tags=['key_leak', 'high_risk']
        )
        assets_created.append(asset)
    
    db.commit()
    return assets_created


def _get_or_create_ai_asset(
    db: Session,
    org_id: str,
    asset_type: str,
    name: str,
    evidence: Dict[str, Any],
    source: str,
    risk_tags: List[str] = None,
    repository: str = None,
    file_path: str = None
) -> AIAsset:
    """Get or create an AI asset record."""
    # Check if exists
    existing = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.type == asset_type,
        AIAsset.name == name
    ).first()
    
    if existing:
        # Update last seen
        existing.last_seen_at = datetime.now(timezone.utc)
        if risk_tags:
            current_tags = existing.risk_tags or []
            existing.risk_tags = list(set(current_tags + risk_tags))
        # Merge evidence
        current_evidence = existing.evidence or {}
        current_evidence.update(evidence)
        existing.evidence = current_evidence
        return existing
    
    # Create new
    asset = AIAsset(
        org_id=org_id,
        type=asset_type,
        name=name,
        evidence=evidence,
        risk_tags=risk_tags or [],
        source=source,
        repository=repository,
        file_path=file_path,
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc)
    )
    db.add(asset)
    return asset


# =============================================================================
# AI Posture Score Calculation
# =============================================================================

def calculate_ai_posture_score(
    db: Session,
    org_id: str
) -> Tuple[int, str, int]:
    """
    Calculate deterministic AI posture score for an organization.
    
    Score components:
    - Base: 100 (clean)
    - Each key leak: -30
    - Each agent framework: -10
    - Each unguarded model provider: -5
    - Each high-risk tag: -5
    - Bonus if guardrails detected: +10
    
    Returns: (score 0-100, status, trend)
    """
    # Get AI assets
    ai_assets = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.status == 'active'
    ).all()
    
    score = 100
    
    # Count by type and risk
    key_leaks = 0
    agent_frameworks = 0
    high_risk_tags = 0
    has_guardrails = False
    
    for asset in ai_assets:
        if 'key_leak' in (asset.risk_tags or []):
            key_leaks += 1
        if asset.type == 'agent_framework':
            agent_frameworks += 1
        if 'high_risk' in (asset.risk_tags or []):
            high_risk_tags += 1
        if 'guardrails' in asset.name.lower() or 'lakera' in asset.name.lower():
            has_guardrails = True
    
    # Apply penalties
    score -= key_leaks * 30
    score -= agent_frameworks * 10
    score -= high_risk_tags * 5
    
    # Apply bonus for guardrails
    if has_guardrails:
        score += 10
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Determine status
    if score >= 80:
        status = 'clean'
    elif score >= 50:
        status = 'warning'
    else:
        status = 'critical'
    
    # Calculate trend (compare to last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    old_assets = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.first_seen_at < thirty_days_ago
    ).count()
    
    new_assets = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.first_seen_at >= thirty_days_ago
    ).count()
    
    # Trend is negative if new risky assets were added
    trend = -new_assets * 5 if new_assets > 0 else 0
    
    return score, status, trend


# =============================================================================
# AI Risk Signal Generation
# =============================================================================

def generate_ai_risk_signals(
    org_id: str,
    ai_assets: List[AIAsset],
    db: Session
) -> List[Dict[str, Any]]:
    """
    Generate AI-specific risk signals based on detected assets.
    
    Signal rules:
    - Prompt leakage risk: prompt files in public repos
    - Agent tooling exposure: agent framework + risky patterns
    - No guardrails detected: no mention of safety tools
    - Key leak risk: exposed API keys
    """
    signals = []
    
    for asset in ai_assets:
        if 'key_leak' in (asset.risk_tags or []):
            signals.append({
                'type': 'ai_key_leak',
                'severity': 'critical',
                'category': 'ai',
                'title': f'Exposed {asset.name} API Key',
                'detail': f"An API key for {asset.name} was detected in a public repository. This should be rotated immediately.",
                'evidence': asset.evidence,
                'ai_asset_id': asset.id
            })
        
        if asset.type == 'agent_framework' and 'agent_framework' in (asset.risk_tags or []):
            signals.append({
                'type': 'ai_agent_exposure',
                'severity': 'medium',
                'category': 'ai',
                'title': f'{asset.name} Agent Framework Detected',
                'detail': f"The {asset.name} agent framework is in use. Ensure proper guardrails and access controls are in place.",
                'evidence': asset.evidence,
                'ai_asset_id': asset.id
            })
    
    return signals


# =============================================================================
# AI Governance Summary
# =============================================================================

def get_ai_governance_summary(
    db: Session,
    org_id: str
) -> Dict[str, Any]:
    """
    Get comprehensive AI governance summary for the organization.
    """
    # Get AI assets
    ai_assets = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.status == 'active'
    ).all()
    
    # Calculate posture score
    score, status, trend = calculate_ai_posture_score(db, org_id)
    
    # Count by type
    assets_by_type = {}
    for asset in ai_assets:
        assets_by_type[asset.type] = assets_by_type.get(asset.type, 0) + 1
    
    # Get top AI risks (signals with category='ai')
    top_risks = db.query(Signal).filter(
        Signal.org_id == org_id,
        Signal.category == 'ai'
    ).order_by(Signal.created_at.desc()).limit(5).all()
    
    # Get AI-related decisions this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    ai_decisions = db.query(SecurityDecision).join(Scan).filter(
        Scan.org_id == org_id,
        SecurityDecision.created_at >= week_ago,
        SecurityDecision.action_id.in_(['key-rotation', 'review-agents', 'audit-ai-tools'])
    ).all()
    
    return {
        'ai_posture_score': score,
        'ai_posture_status': status,
        'ai_posture_trend': trend,
        'assets_by_type': assets_by_type,
        'total_ai_assets': len(ai_assets),
        'top_ai_risks': top_risks,
        'ai_decisions_this_week': ai_decisions,
        'last_updated': datetime.now(timezone.utc)
    }


def get_ai_assets_list(
    db: Session,
    org_id: str,
    asset_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[AIAsset], int]:
    """
    Get paginated list of AI assets.
    """
    query = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.status == 'active'
    )
    
    if asset_type:
        query = query.filter(AIAsset.type == asset_type)
    
    total = query.count()
    assets = query.order_by(AIAsset.last_seen_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return assets, total
