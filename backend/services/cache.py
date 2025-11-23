from datetime import datetime, timedelta
import hashlib
import json
import time
from typing import Any, Awaitable, Callable, List, Tuple

from sqlalchemy.orm import Session

from ..logging_config import log_service_call
from ..models import CacheEntry
from ..schemas import Signal


def cache_key(namespace: str, payload: dict) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:24]
    return f"{namespace}:{digest}"


async def get_cached_or_fetch(
    session: Session,
    key: str,
    ttl_seconds: int,
    fetcher: Callable[[], Awaitable[Any]],
    service_name: str = "cache",
) -> Any:
    """Get cached value or fetch and cache it."""
    start_time = time.time()
    entry = session.get(CacheEntry, key)
    now = datetime.utcnow()
    
    if entry and entry.expires_at > now:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service=service_name,
            latency_ms=latency_ms,
            cache_hit=True,
            success=True,
        )
        return entry.value

    data = await fetcher()
    expires_at = now + timedelta(seconds=ttl_seconds)
    session.merge(CacheEntry(key=key, value=data, expires_at=expires_at))
    session.flush()
    
    latency_ms = (time.time() - start_time) * 1000
    log_service_call(
        service=service_name,
        latency_ms=latency_ms,
        cache_hit=False,
        success=True,
    )
    return data


async def cached_signal_bundle(
    session: Session,
    namespace: str,
    payload: dict,
    ttl_seconds: int,
    fetcher: Callable[[], Awaitable[Tuple[dict, List[Signal]]]],
) -> Tuple[dict, List[Signal]]:
    """Get cached signal bundle or fetch and cache it."""
    start_time = time.time()
    key = cache_key(namespace, payload)
    entry = session.get(CacheEntry, key)
    now = datetime.utcnow()
    
    if entry and entry.expires_at > now:
        value = entry.value
        signals = [Signal(**signal) for signal in value.get("signals", [])]
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service=namespace,
            latency_ms=latency_ms,
            cache_hit=True,
            success=True,
        )
        return value.get("metadata", {}), signals

    metadata, signals = await fetcher()
    expires_at = now + timedelta(seconds=ttl_seconds)
    value = {
        "metadata": metadata,
        "signals": [signal.model_dump(mode="json") for signal in signals],
    }
    session.merge(CacheEntry(key=key, value=value, expires_at=expires_at))
    session.flush()
    
    latency_ms = (time.time() - start_time) * 1000
    log_service_call(
        service=namespace,
        latency_ms=latency_ms,
        cache_hit=False,
        success=True,
    )
    return metadata, signals
