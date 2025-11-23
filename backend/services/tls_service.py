import asyncio
import socket
import ssl
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from ..schemas import Signal
from .signal_factory import make_signal


def _sync_fetch(domain: str) -> Dict:
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=domain)
    conn.settimeout(8.0)
    conn.connect((domain, 443))
    cert = conn.getpeercert()
    conn.close()
    return cert


async def fetch_tls_metadata(domain: str) -> Tuple[Dict, List[Signal]]:
    metadata: Dict = {}
    signals: List[Signal] = []

    try:
        cert = await asyncio.to_thread(_sync_fetch, domain)
        san = cert.get("subjectAltName")
        if san:
            san = [entry[1] for entry in san if isinstance(entry, tuple) and len(entry) > 1]
        metadata = {
            "issuer": str(cert.get("issuer")),
            "subject": str(cert.get("subject")),
            "subjectAltName": san,
            "notAfter": cert.get("notAfter"),
        }
        not_after_str = cert.get("notAfter")
        if not_after_str:
            expiry = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days = (expiry - datetime.now(timezone.utc)).days
            metadata["days_to_expiry"] = days
            if days < 30:
                signals.append(
                    make_signal(
                        signal_id="tls_expiring_soon",
                        signal_type="tls",
                        detail="TLS certificate expires within 30 days",
                        severity="high",
                        category="network",
                        source="tls",
                        url=f"https://{domain}",
                        raw={"days_remaining": days},
                    )
                )
    except Exception:
        signals.append(
            make_signal(
                signal_id="tls_unreachable",
                signal_type="tls",
                detail="Unable to obtain TLS certificate",
                severity="high",
                category="network",
                source="tls",
                url=f"https://{domain}",
                raw={},
            )
        )

    return metadata, signals
