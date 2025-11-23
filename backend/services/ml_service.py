from typing import Dict, List

from ..schemas import Signal


def estimate_likelihoods(signals: List[Signal]) -> Dict[str, float]:
    severity_weights = {"high": 0.2, "medium": 0.1, "low": 0.05}
    score = 0.0
    for signal in signals:
        score += severity_weights.get(signal.severity, 0)
    score = min(1.0, score)
    return {
        "breach_likelihood_30d": round(min(1.0, score + 0.05), 2),
        "breach_likelihood_90d": round(min(1.0, score + 0.15), 2),
    }
