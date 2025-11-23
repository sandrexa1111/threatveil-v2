from typing import Dict, List, Tuple

import httpx

from ..config import settings
from ..schemas import Signal
from .signal_factory import make_signal
from .utils import with_backoff

TIMEOUT = httpx.Timeout(20.0, read=20.0, write=10.0, connect=5.0)
USER_AGENT = settings.user_agent

SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]


async def _fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    return await with_backoff(lambda: client.get(url))


async def fetch_http_metadata(domain: str) -> Tuple[Dict, List[Signal], List[str]]:
    metadata: Dict = {"https": None, "http": None, "headers": {}, "redirect_to_https": False}
    signals: List[Signal] = []
    tech_tokens: List[str] = []

    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
        https_url = f"https://{domain}"
        try:
            https_resp = await _fetch(client, https_url)
            metadata["https"] = {
                "status": https_resp.status_code,
                "headers": dict(https_resp.headers),
            }
            metadata["headers"] = {k.lower(): v for k, v in https_resp.headers.items()}
            server = https_resp.headers.get("Server")
            powered_by = https_resp.headers.get("X-Powered-By")
            generator = https_resp.headers.get("X-Generator")
            for token in (server, powered_by, generator):
                if token:
                    tech_tokens.append(token)
        except httpx.HTTPError:
            signals.append(
                make_signal(
                    signal_id="http_https_unreachable",
                    signal_type="http",
                    detail="HTTPS endpoint unreachable",
                    severity="high",
                    category="network",
                    source="https",
                    url=https_url,
                    raw={},
                )
            )

        http_url = f"http://{domain}"
        try:
            resp = await with_backoff(lambda: client.get(http_url, follow_redirects=False))
            metadata["http"] = {"status": resp.status_code, "headers": dict(resp.headers)}
            if resp.is_redirect:
                location = resp.headers.get("location", "")
                if location.startswith("https://"):
                    metadata["redirect_to_https"] = True
            else:
                signals.append(
                    make_signal(
                        signal_id="http_no_https_redirect",
                        signal_type="http",
                        detail="HTTP endpoint does not enforce HTTPS redirect",
                        severity="high",
                        category="network",
                        source="http",
                        url=http_url,
                        raw={"status": resp.status_code},
                    )
                )
        except httpx.HTTPError:
            pass

    headers_lower = metadata.get("headers", {})
    if headers_lower:
        for header in SECURITY_HEADERS:
            if header not in headers_lower:
                severity = "high" if header in ("strict-transport-security", "content-security-policy") else "medium"
                signals.append(
                    make_signal(
                        signal_id=f"http_header_{header.replace('-', '_')}_missing",
                        signal_type="http",
                        detail=f"Missing {header.title()} header",
                        severity=severity,
                        category="software",
                        source="https",
                        url=f"https://{domain}",
                        raw={"headers": list(headers_lower.keys())},
                    )
                )

    tech_tokens = list({token for token in tech_tokens if token})
    return metadata, signals, tech_tokens
