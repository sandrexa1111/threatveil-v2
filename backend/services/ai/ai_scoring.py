"""AI risk scoring for ThreatVeil Horizon features."""
from typing import Dict, List, Optional


def compute_ai_score(
    ai_tools: Optional[List[str]] = None,
    ai_vendors: Optional[List[Dict]] = None,
    ai_keys: Optional[List[Dict]] = None,
) -> int:
    """
    Compute AI risk score based on detected AI tools, vendors, and key leaks.
    
    Scoring logic (MVP):
    - Base score from number of AI tools (more tools → more complexity):
      - 0 tools → 0 pts
      - 1–3 tools → 10 pts
      - 4+ tools → 20 pts
    - Add 30 pts for each high-severity AI key leak (cap total from leaks at 60 pts).
    - Add 10 pts if any "agent" or complex orchestration detected.
    - Clamp score to 0..100.
    
    Args:
        ai_tools: List of detected AI tools/frameworks (e.g., ["openai", "langchain"])
        ai_vendors: List of AI vendors with risk metadata (not used in MVP)
        ai_keys: List of detected AI key leak signals/metadata
    
    Returns:
        AI risk score (0-100)
    """
    score = 0
    
    # Base score from number of AI tools
    tool_count = len(ai_tools) if ai_tools else 0
    if tool_count == 0:
        base_score = 0
    elif 1 <= tool_count <= 3:
        base_score = 10
    else:  # 4+ tools
        base_score = 20
    
    score += base_score
    
    # Add points for AI key leaks (high severity)
    key_leak_count = len(ai_keys) if ai_keys else 0
    if key_leak_count > 0:
        # 30 pts per leak, capped at 60 pts total
        leak_points = min(key_leak_count * 30, 60)
        score += leak_points
    
    # Add points if agent/orchestration detected
    # Check if any tools suggest agent usage
    agent_keywords = ["langchain", "crewai", "autogen", "langgraph", "agent"]
    has_agent = False
    if ai_tools:
        tools_lower = [tool.lower() for tool in ai_tools]
        has_agent = any(keyword in tool for tool in tools_lower for keyword in agent_keywords)
    
    if has_agent:
        score += 10
    
    # Clamp to 0-100
    return max(0, min(100, score))
