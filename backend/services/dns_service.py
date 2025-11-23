from typing import Dict, List, Tuple

import dns.asyncresolver
import dns.exception

from ..schemas import Signal
from .signal_factory import make_signal

resolver = dns.asyncresolver.Resolver()
resolver.lifetime = 5.0


async def _lookup(domain: str, record_type: str) -> List[str]:
    try:
        answers = await resolver.resolve(domain, record_type)
        return [answer.to_text() for answer in answers]
    except (dns.exception.DNSException, ValueError):
        return []


async def fetch_dns_metadata(domain: str) -> Tuple[Dict[str, List[str]], List[Signal]]:
    metadata = {
        "A": await _lookup(domain, "A"),
        "AAAA": await _lookup(domain, "AAAA"),
        "MX": await _lookup(domain, "MX"),
        "TXT": await _lookup(domain, "TXT"),
        "DMARC": await _lookup(f"_dmarc.{domain}", "TXT"),
    }

    signals: List[Signal] = []
    if not metadata["DMARC"]:
        signals.append(
            make_signal(
                signal_id="dns_missing_dmarc",
                signal_type="dns",
                detail="Missing DMARC record",
                severity="medium",
                category="data_exposure",
                source="dns",
                url=None,
                raw={"records": metadata},
            )
        )

    spf_present = any("v=spf" in txt.lower() for txt in metadata["TXT"])
    if not spf_present:
        signals.append(
            make_signal(
                signal_id="dns_missing_spf",
                signal_type="dns",
                detail="No SPF record detected",
                severity="medium",
                category="network",
                source="dns",
                raw={"records": metadata.get("TXT")},
            )
        )

    return metadata, signals
