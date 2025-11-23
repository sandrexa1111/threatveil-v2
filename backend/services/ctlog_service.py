import httpx
from typing import Dict, List, Tuple

from ..schemas import Signal
from .signal_factory import make_signal
from .utils import with_backoff

TIMEOUT = httpx.Timeout(20.0, connect=5.0)


async def fetch_ct_logs(domain: str) -> Tuple[Dict, List[Signal]]:
    url = f"https://crt.sh/?q={domain}&output=json"
    metadata: Dict = {"entries": []}
    signals: List[Signal] = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await with_backoff(lambda: client.get(url))
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    data = []
                unique_ids = {entry.get("id"): entry for entry in data if isinstance(entry, dict)}
                metadata["entries"] = list(unique_ids.values())
                count = len(unique_ids)
                metadata["count"] = count
                if count > 50:
                    signals.append(
                        make_signal(
                            signal_id="ct_high_churn",
                            signal_type="ct",
                            detail="High number of recent CT log entries",
                            severity="medium",
                            category="network",
                            source="ctlog",
                            url=url,
                            raw={"count": count},
                        )
                    )
        except httpx.HTTPError:
            signals.append(
                make_signal(
                    signal_id="ct_fetch_failed",
                    signal_type="ct",
                    detail="Unable to retrieve certificate transparency logs",
                    severity="low",
                    category="network",
                    source="ctlog",
                    url=url,
                    raw={},
                )
            )

    return metadata, signals
