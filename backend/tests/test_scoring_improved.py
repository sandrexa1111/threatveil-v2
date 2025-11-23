"""Improved tests for scoring and likelihood estimation."""
import pytest

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scoring import score_signals
from backend.services.ml_service import estimate_likelihoods
from backend.schemas import Signal, Evidence, Category, Severity
from datetime import datetime, timezone


def make_test_signal(
    signal_id: str,
    severity: Severity,
    category: Category,
) -> Signal:
    """Helper to create test signals."""
    return Signal(
        id=signal_id,
        type="http",
        detail="Test signal",
        severity=severity,
        category=category,
        evidence=Evidence(
            source="test",
            observed_at=datetime.now(timezone.utc),
            raw={},
        ),
    )


def test_scoring_no_signals():
    """Test scoring with no signals returns 0."""
    score, categories = score_signals([])
    assert score == 0
    assert all(c.score == 0 for c in categories.values())


def test_scoring_single_high_severity():
    """Test scoring with a single high severity signal."""
    signals = [make_test_signal("test1", "high", "network")]
    score, categories = score_signals(signals)
    # High = 30 points, network weight = 0.4, so 30 * 0.4 = 12
    assert score == 12
    assert categories["network"].score == 30


def test_scoring_multiple_categories():
    """Test scoring across multiple categories."""
    signals = [
        make_test_signal("n1", "high", "network"),  # 30 points
        make_test_signal("s1", "medium", "software"),  # 15 points
        make_test_signal("d1", "low", "data_exposure"),  # 5 points
    ]
    score, categories = score_signals(signals)
    # network: 30 * 0.4 = 12
    # software: 15 * 0.35 = 5.25
    # data_exposure: 5 * 0.2 = 1
    # Total: ~18 (rounded)
    assert 15 <= score <= 20
    assert categories["network"].score == 30
    assert categories["software"].score == 15
    assert categories["data_exposure"].score == 5


def test_scoring_capped_at_100():
    """Test that score is capped at 100."""
    # Create many high severity signals
    signals = [make_test_signal(f"test{i}", "high", "network") for i in range(10)]
    score, categories = score_signals(signals)
    assert score <= 100
    assert categories["network"].score <= 100


def test_likelihood_estimation_no_signals():
    """Test likelihood estimation with no signals."""
    likelihoods = estimate_likelihoods([])
    assert likelihoods["breach_likelihood_30d"] >= 0.0
    assert likelihoods["breach_likelihood_30d"] <= 1.0
    assert likelihoods["breach_likelihood_90d"] >= 0.0
    assert likelihoods["breach_likelihood_90d"] <= 1.0
    assert likelihoods["breach_likelihood_90d"] >= likelihoods["breach_likelihood_30d"]


def test_likelihood_estimation_boundaries():
    """Test likelihood estimation at boundaries."""
    # Low signals
    low_signals = [make_test_signal("l1", "low", "network") for _ in range(5)]
    low_likelihoods = estimate_likelihoods(low_signals)
    assert 0.0 <= low_likelihoods["breach_likelihood_30d"] <= 1.0
    
    # High signals
    high_signals = [make_test_signal("h1", "high", "network") for _ in range(10)]
    high_likelihoods = estimate_likelihoods(high_signals)
    assert 0.0 <= high_likelihoods["breach_likelihood_30d"] <= 1.0
    assert high_likelihoods["breach_likelihood_30d"] > low_likelihoods["breach_likelihood_30d"]


def test_likelihood_90d_higher_than_30d():
    """Test that 90d likelihood is always >= 30d likelihood."""
    signals = [make_test_signal("test1", "medium", "software")]
    likelihoods = estimate_likelihoods(signals)
    assert likelihoods["breach_likelihood_90d"] >= likelihoods["breach_likelihood_30d"]


def test_likelihood_capped_at_1():
    """Test that likelihoods are capped at 1.0."""
    # Many high severity signals
    signals = [make_test_signal(f"h{i}", "high", "network") for i in range(20)]
    likelihoods = estimate_likelihoods(signals)
    assert likelihoods["breach_likelihood_30d"] <= 1.0
    assert likelihoods["breach_likelihood_90d"] <= 1.0

