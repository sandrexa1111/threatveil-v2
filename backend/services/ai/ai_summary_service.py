"""AI-specific summary generation for ThreatVeil Horizon."""
import time
from typing import Dict, List, Optional

import httpx

from ...config import settings
from ...logging_config import log_service_call
from ..utils import with_backoff

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3:generateContent"

TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)


def fallback_ai_summary(
    ai_tools: List[str],
    ai_keys: List[Dict],
    domain: str,
    company_name: Optional[str] = None,
) -> str:
    """
    Generate a deterministic fallback AI summary.
    
    Args:
        ai_tools: List of detected AI tools
        ai_keys: List of detected AI key leaks
        domain: Domain name
        company_name: Optional company name
    
    Returns:
        Fallback summary string
    """
    company_label = company_name or domain
    
    if not ai_tools and not ai_keys:
        return (
            f"No obvious AI usage detected for {company_label} in public repositories. "
            "This may indicate limited AI integration or private repositories not accessible via GitHub."
        )
    
    if ai_keys:
        key_count = len(ai_keys)
        key_types = [k.get("key_type", "unknown") for k in ai_keys]
        unique_types = ", ".join(set(key_types))
        
        return (
            f"We detected {key_count} potential AI key leak(s) ({unique_types}) for {company_label}. "
            "Immediate action required: rotate exposed keys, remove them from public repositories, "
            "and store secrets in a secure vault. Review GitHub repositories for additional exposed credentials."
        )
    
    # Has tools but no keys
    tool_list = ", ".join(ai_tools[:5])  # Limit to first 5
    if len(ai_tools) > 5:
        tool_list += f" and {len(ai_tools) - 5} more"
    
    return (
        f"AI tools detected for {company_label}: {tool_list}. "
        "No obvious key leaks found in public repositories. "
        "Consider reviewing AI integration security practices and ensuring API keys are stored securely."
    )


async def generate_ai_summary(
    ai_tools: List[str],
    ai_keys: List[Dict],
    ai_score: int,
    domain: str,
    company_name: Optional[str] = None,
) -> str:
    """
    Generate an AI-focused summary using Gemini API with fallback.
    
    Args:
        ai_tools: List of detected AI tools
        ai_keys: List of detected AI key leaks
        ai_score: Computed AI risk score
        domain: Domain name
        company_name: Optional company name
    
    Returns:
        AI summary string
    """
    if not settings.gemini_api_key:
        log_service_call(
            service="gemini_ai_summary",
            latency_ms=0.0,
            cache_hit=False,
            success=False,
            error="API key missing",
        )
        return fallback_ai_summary(ai_tools, ai_keys, domain, company_name)
    
    start_time = time.time()
    
    # Build prompt
    company_label = company_name or domain
    tools_text = ", ".join(ai_tools) if ai_tools else "None detected"
    keys_text = f"{len(ai_keys)} key leak(s) detected" if ai_keys else "No key leaks detected"
    
    prompt = (
        "You are Horizon Analyst. Explain the AI-related risks for this company in plain language. "
        "Mention:\n"
        f"- Which AI tools seem to be in use: {tools_text}\n"
        f"- Whether there are any exposed AI keys: {keys_text}\n"
        f"- How complex or fragile the AI setup looks (score: {ai_score}/100)\n"
        "Provide 3 prioritized action steps. Keep it under 160 words.\n\n"
        f"Company: {company_label}"
    )
    
    params = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "topK": 40,
            "topP": 0.9,
            "maxOutputTokens": 400,
        },
        "safetySettings": [],
    }
    
    url = f"{BASE_URL}?key={settings.gemini_api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.post(url, json=params),
                retries=3,
                base_delay=0.2,
                max_delay=2.5,
            )
            latency_ms = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            # Extract text from Gemini response
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    summary = parts[0]["text"].strip()
                    
                    log_service_call(
                        service="gemini_ai_summary",
                        latency_ms=latency_ms,
                        cache_hit=False,
                        success=True,
                    )
                    return summary
            
            # If response structure is unexpected, use fallback
            log_service_call(
                service="gemini_ai_summary",
                latency_ms=latency_ms,
                cache_hit=False,
                success=False,
                error="Unexpected response structure",
            )
            return fallback_ai_summary(ai_tools, ai_keys, domain, company_name)
    
    except httpx.HTTPStatusError as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:100]}"
        log_service_call(
            service="gemini_ai_summary",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=error_msg,
        )
        return fallback_ai_summary(ai_tools, ai_keys, domain, company_name)
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="gemini_ai_summary",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        return fallback_ai_summary(ai_tools, ai_keys, domain, company_name)

