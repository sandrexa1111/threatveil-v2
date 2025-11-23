import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional

import jwt
from fastapi import HTTPException, Request, status

from .config import settings

JWT_ALG = "HS256"
RATE_LIMIT = settings.rate_limit_per_minute
_ip_requests: Dict[str, Deque[float]] = defaultdict(deque)


def _secret() -> str:
    """Get JWT secret from settings."""
    if not settings.jwt_secret or settings.jwt_secret == "change_me":
        raise RuntimeError("JWT_SECRET must be configured")
    return settings.jwt_secret


def create_jwt(payload: dict, expires_minutes: int = 30) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    data = {**payload, "exp": exp}
    return jwt.encode(data, _secret(), algorithm=JWT_ALG)


def verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[JWT_ALG])
    except jwt.PyJWTError as exc:  # pragma: no cover (defensive)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def enforce_rate_limit(request: Request) -> None:
    """Enforce rate limiting using IP address and optionally domain."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Use IP as the base key
    rate_limit_key = client_ip
    
    # For scan endpoints, we could add domain to the key, but that requires reading the body
    # For now, we'll use IP-based rate limiting which is simpler and still effective
    # The domain validation will prevent abuse of the scan endpoint
    
    now = time.time()
    window_start = now - 60
    bucket = _ip_requests[rate_limit_key]

    # Clean old entries outside the 1-minute window
    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in 1 minute.",
        )

    bucket.append(now)
