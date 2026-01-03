"""AI-specific GitHub scanning for ThreatVeil Horizon features."""
import time
from typing import Dict, List, Set, Tuple

import httpx

from ...config import settings
from ...logging_config import log_service_call
from ...schemas import Signal
from ..signal_factory import make_signal, make_service_error_signal
from ..utils import with_backoff

TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)
SEARCH_URL = "https://api.github.com/search/code"

# AI libraries to detect
AI_LIBRARIES = [
    "openai",
    "anthropic",
    "langchain",
    "llama_index",
    "google.generativeai",
    "vertexai",
    "cohere",
    "huggingface",
    "transformers",
    "torch",
    "tensorflow",
    "pytorch",
]

# AI file patterns
AI_FILE_PATTERNS = [
    "*.prompt",
    "*.ai",
    "*.llm.yaml",
    "ai-config.json",
    "prompt_config.*",
    "prompts/*",
    "*.prompt.yaml",
    "*.prompt.yml",
]

# AI agent keywords
AI_AGENT_KEYWORDS = [
    "agent",
    "tool",
    "function_calling",
    "crewAI",
    "AutoGen",
    "LangGraph",
    "autonomous",
    "orchestration",
]


def _build_ai_library_query(org: str) -> str:
    """Build GitHub search query for AI libraries."""
    library_queries = []
    for lib in AI_LIBRARIES:
        # Search for imports and dependencies
        library_queries.append(f'"{lib}"')
        library_queries.append(f"import {lib}")
        library_queries.append(f"from {lib}")
        library_queries.append(f'"{lib}" filename:requirements.txt')
        library_queries.append(f'"{lib}" filename:package.json')
        library_queries.append(f'"{lib}" filename:pyproject.toml')
    
    query = f"org:{org} ({' OR '.join(library_queries[:30])})"  # GitHub limits query length
    return query


def _build_ai_file_query(org: str) -> str:
    """Build GitHub search query for AI-related files."""
    file_queries = []
    for pattern in AI_FILE_PATTERNS:
        if "*" in pattern:
            # Convert glob to GitHub filename search
            base = pattern.replace("*", "")
            file_queries.append(f'filename:{base}')
        else:
            file_queries.append(f'filename:{pattern}')
    
    query = f"org:{org} ({' OR '.join(file_queries)})"
    return query


def _build_ai_agent_query(org: str) -> str:
    """Build GitHub search query for AI agent configurations."""
    agent_queries = []
    for keyword in AI_AGENT_KEYWORDS:
        agent_queries.append(f'"{keyword}"')
        agent_queries.append(f'"{keyword}" filename:*.yaml')
        agent_queries.append(f'"{keyword}" filename:*.yml')
        agent_queries.append(f'"{keyword}" filename:*.json')
    
    query = f"org:{org} ({' OR '.join(agent_queries[:20])})"
    return query


async def _github_search(org: str, query: str) -> Tuple[List[Dict], bool]:
    """Perform a GitHub code search."""
    if not org or not settings.github_token:
        return [], False
    
    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"q": query, "per_page": 30}
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.get(SEARCH_URL, params=params, headers=headers),
                retries=2,
                base_delay=0.2,
                max_delay=2.0,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            
            results = []
            for item in items:
                results.append({
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "repository": item.get("repository", {}).get("full_name"),
                    "html_url": item.get("html_url"),
                    "sha": item.get("sha"),
                })
            
            return results, True
    except Exception as e:
        log_service_call(
            service="github_ai",
            latency_ms=0,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        return [], False


async def detect_ai_libraries(github_org: str) -> Tuple[List[Dict], List[str]]:
    """
    Detect AI libraries and frameworks in GitHub repositories.
    
    Args:
        github_org: GitHub organization name to search
    
    Returns:
        Tuple of (detected_libraries_metadata, detected_library_names)
    """
    if not github_org or not settings.github_token:
        return [], []
    
    query = _build_ai_library_query(github_org)
    results, success = await _github_search(github_org, query)
    
    if not success:
        return [], []
    
    # Extract unique library names from results
    detected_libs: Set[str] = set()
    library_metadata = []
    
    for result in results:
        path_lower = result.get("path", "").lower()
        repo = result.get("repository", "")
        
        # Check which libraries are mentioned
        for lib in AI_LIBRARIES:
            if lib in path_lower or lib in result.get("name", "").lower():
                detected_libs.add(lib)
                library_metadata.append({
                    "library": lib,
                    "repository": repo,
                    "path": result.get("path"),
                    "url": result.get("html_url"),
                })
    
    return library_metadata, sorted(list(detected_libs))


async def detect_ai_files(github_org: str) -> Tuple[List[Dict], List[str]]:
    """
    Detect AI-related files in GitHub repositories.
    
    Args:
        github_org: GitHub organization name to search
    
    Returns:
        Tuple of (detected_files_metadata, detected_file_paths)
    """
    if not github_org or not settings.github_token:
        return [], []
    
    query = _build_ai_file_query(github_org)
    results, success = await _github_search(github_org, query)
    
    if not success:
        return [], []
    
    file_metadata = []
    file_paths = []
    
    for result in results:
        path = result.get("path", "")
        if path:
            file_metadata.append({
                "path": path,
                "repository": result.get("repository"),
                "url": result.get("html_url"),
            })
            file_paths.append(path)
    
    return file_metadata, file_paths


async def detect_ai_agent_configs(github_org: str) -> List[Dict]:
    """
    Detect AI agent configurations in GitHub repositories.
    
    Args:
        github_org: GitHub organization name to search
    
    Returns:
        List of detected agent configurations with metadata
    """
    if not github_org or not settings.github_token:
        return []
    
    query = _build_ai_agent_query(github_org)
    results, success = await _github_search(github_org, query)
    
    if not success:
        return []
    
    agent_configs = []
    
    for result in results:
        path_lower = result.get("path", "").lower()
        # Check if this looks like an agent config file
        if any(keyword in path_lower for keyword in AI_AGENT_KEYWORDS):
            agent_configs.append({
                "type": "agent_config",
                "repository": result.get("repository"),
                "path": result.get("path"),
                "url": result.get("html_url"),
            })
    
    return agent_configs


async def detect_ai_key_leaks(github_org: str) -> Tuple[List[Dict], List[Signal]]:
    """
    Detect AI API key leaks in GitHub repositories.
    
    Args:
        github_org: GitHub organization name to search
    
    Returns:
        Tuple of (leak_metadata, signals)
    """
    if not github_org or not settings.github_token:
        return [], []
    
    # AI key patterns to search for
    key_patterns = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "ANTHROPIC_API_KEY",
        "HUGGINGFACE_TOKEN",
        "FIREBASE_SERVICE_ACCOUNT",
        ".env.production",
        "ANTHROPIC_API_KEY",
        "COHERE_API_KEY",
    ]
    
    query_parts = []
    for pattern in key_patterns:
        query_parts.append(f'"{pattern}"')
        query_parts.append(f'filename:.env* "{pattern}"')
    
    query = f"org:{github_org} ({' OR '.join(query_parts)})"
    
    results, success = await _github_search(github_org, query)
    
    if not success:
        return [], []
    
    leak_metadata = []
    signals = []
    
    for result in results:
        path = result.get("path", "")
        repo = result.get("repository", "")
        
        # Determine which key type was detected
        key_type = "unknown"
        for pattern in key_patterns:
            if pattern in path or pattern in result.get("name", ""):
                key_type = pattern.replace("_API_KEY", "").replace("_TOKEN", "").lower()
                break
        
        leak_info = {
            "key_type": key_type,
            "repository": repo,
            "path": path,
            "url": result.get("html_url"),
        }
        leak_metadata.append(leak_info)
        
        # Create signal
        signal_id = f"ai_leak_{key_type}_key"
        signals.append(
            make_signal(
                signal_id=signal_id,
                signal_type="ai_guard",
                detail=f"Potential {key_type.upper()} API key exposure in {repo}/{path}",
                severity="high",
                category="ai_integration",
                source="github",
                url=result.get("html_url"),
                raw=leak_info,
            )
        )
    
    return leak_metadata, signals


async def scan_github_for_ai_indicators(github_org: str) -> Dict:
    """
    Comprehensive AI indicator scan for GitHub organization.
    
    Args:
        github_org: GitHub organization name to search
    
    Returns:
        Dict with keys:
        - ai_libraries: List of detected AI libraries
        - ai_files: List of detected AI-related files
        - ai_agents: List of detected AI agent configurations
        - ai_keys: List of detected AI key leaks
        - summary: Summary of AI usage patterns
    """
    if not github_org or not settings.github_token:
        return {
            "ai_libraries": [],
            "ai_files": [],
            "ai_agents": [],
            "ai_keys": [],
            "summary": {
                "total_libraries": 0,
                "total_files": 0,
                "total_agents": 0,
                "total_key_leaks": 0,
            },
        }
    
    # Run all detections in parallel
    import asyncio
    
    libraries_meta, library_names = await detect_ai_libraries(github_org)
    files_meta, file_paths = await detect_ai_files(github_org)
    agents = await detect_ai_agent_configs(github_org)
    key_leaks, _ = await detect_ai_key_leaks(github_org)
    
    return {
        "ai_libraries": libraries_meta,
        "ai_files": files_meta,
        "ai_agents": agents,
        "ai_keys": key_leaks,
        "summary": {
            "total_libraries": len(library_names),
            "total_files": len(file_paths),
            "total_agents": len(agents),
            "total_key_leaks": len(key_leaks),
        },
    }
