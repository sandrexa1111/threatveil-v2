import time
from typing import Dict, List

import httpx

from ..config import settings
from ..logging_config import log_service_call
from ..schemas import Signal
from .cache import cache_key, get_cached_or_fetch
from .signal_factory import make_signal
from .utils import with_backoff

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)


def _summary_payload(signals: List[Signal], risk_score: int, likelihoods: Dict[str, float]) -> Dict:
    return {
        "risk_score": risk_score,
        "likelihoods": likelihoods,
        "signals": [
            {"id": s.id, "severity": s.severity, "category": s.category, "detail": s.detail}
            for s in signals[:12]
        ],
    }


def fallback_summary(signals: List[Signal], risk_score: int, likelihoods: Dict[str, float]) -> str:
    high = [s.detail for s in signals if s.severity == "high"][:3]
    medium = [s.detail for s in signals if s.severity == "medium"][:2]
    bullets = "; ".join(high + medium) if high or medium else "No critical misconfigurations detected."
    return (
        f"Risk score {risk_score}/100. Focus on {bullets}. "
        f"Estimated breach likelihood: {likelihoods['breach_likelihood_30d']*100:.0f}% (30d) "
        f"and {likelihoods['breach_likelihood_90d']*100:.0f}% (90d)."
    )


async def summarize(session, signals: List[Signal], risk_score: int, likelihoods: Dict[str, float]) -> str:
    bundle = _summary_payload(signals, risk_score, likelihoods)
    key = cache_key("gemini", bundle)

    async def _call_api() -> str:
        if not settings.gemini_api_key:
            log_service_call(
                service="gemini",
                latency_ms=0.0,
                cache_hit=False,
                success=False,
                error="API key missing",
            )
            return fallback_summary(signals, risk_score, likelihoods)

        start_time = time.time()
        prompt = (
            "SYSTEM: You are Veil Analyst. Provide ≤120 words summary and 2 short remediation actions.\n"
            f"USER: {bundle}"
        )
        params = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.9,
                "maxOutputTokens": 300,
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

                if response.status_code != 200:
                    log_service_call(
                        service="gemini",
                        latency_ms=latency_ms,
                        cache_hit=False,
                        success=False,
                        error=f"HTTP {response.status_code}",
                    )
                    return fallback_summary(signals, risk_score, likelihoods)

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    log_service_call(
                        service="gemini",
                        latency_ms=latency_ms,
                        cache_hit=False,
                        success=False,
                        error="No candidates in response",
                    )
                    return fallback_summary(signals, risk_score, likelihoods)

                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                words = text.split()
                if len(words) > 120:
                    text = " ".join(words[:120])
                
                log_service_call(
                    service="gemini",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=True,
                )
                return text.strip()
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            log_service_call(
                service="gemini",
                latency_ms=latency_ms,
                cache_hit=False,
                success=False,
                error=str(e),
            )
            return fallback_summary(signals, risk_score, likelihoods)

    return await get_cached_or_fetch(
        session, key, ttl_seconds=60 * 60 * 12, fetcher=_call_api, service_name="gemini"
    )


async def chat_completion(prompt: str) -> str:
    """Generate chat completion using Gemini API."""
    if not settings.gemini_api_key:
        return "Gemini key missing. Please configure GEMINI_API_KEY to enable chat."

    start_time = time.time()
    message = (
        "SYSTEM: You are Veil Analyst. Answer concisely and avoid sharing secrets.\n"
        f"USER: {prompt}"
    )
    params = {
        "contents": [{"parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0.2, "topK": 32, "topP": 0.9, "maxOutputTokens": 256},
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

            if response.status_code != 200:
                log_service_call(
                    service="gemini_chat",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=False,
                    error=f"HTTP {response.status_code}",
                )
                return "Chat service unavailable."

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                log_service_call(
                    service="gemini_chat",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=False,
                    error="No candidates in response",
                )
                return "No response generated."

            log_service_call(
                service="gemini_chat",
                latency_ms=latency_ms,
                cache_hit=False,
                success=True,
            )
            return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="gemini_chat",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        return "Chat service unavailable."
