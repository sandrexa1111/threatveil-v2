from typing import Dict, List, Tuple

from .schemas import Category, CategoryScore, Severity, Signal

SEVERITY_POINTS: Dict[Severity, int] = {"low": 5, "medium": 15, "high": 30, "critical": 50}
CATEGORY_WEIGHTS: Dict[Category, float] = {
    "network": 0.4,
    "software": 0.35,
    "data_exposure": 0.2,
    "ai_integration": 0.05,
}


def _severity_from_score(score: int) -> Severity:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def score_signals(signals: List[Signal]) -> Tuple[int, Dict[Category, CategoryScore]]:
    category_points: Dict[Category, int] = {cat: 0 for cat in CATEGORY_WEIGHTS}
    for signal in signals:
        category_points[signal.category] += SEVERITY_POINTS[signal.severity]

    categories: Dict[Category, CategoryScore] = {}
    total_score = 0.0

    for category, weight in CATEGORY_WEIGHTS.items():
        raw = category_points[category]
        normalized = min(100, raw)
        severity = _severity_from_score(normalized)
        categories[category] = CategoryScore(score=int(normalized), weight=weight, severity=severity)
        total_score += normalized * weight

    return int(min(100, round(total_score))), categories
