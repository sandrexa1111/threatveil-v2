"""Load and provide lookups for the risk registry."""
import json
import os
from pathlib import Path
from typing import Dict, Optional

from ...schemas import Category, Severity


# Cache the loaded registry
_registry_cache: Optional[Dict] = None


def _load_registry() -> Dict:
    """Load risk_registry.json from the backend root."""
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    # Try to find risk_registry.json relative to this file
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent.parent
    registry_path = backend_root / "risk_registry.json"
    
    if not registry_path.exists():
        # Fallback: try backend/app/ or backend/
        alt_paths = [
            backend_root / "app" / "risk_registry.json",
            backend_root / "risk_registry.json",
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                registry_path = alt_path
                break
    
    if not registry_path.exists():
        # Return empty registry if file not found
        _registry_cache = {"signals": {}}
        return _registry_cache
    
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            _registry_cache = json.load(f)
        return _registry_cache
    except (json.JSONDecodeError, IOError) as e:
        # Return empty registry on error
        _registry_cache = {"signals": {}}
        return _registry_cache


def get_signal_info(signal_id: str) -> Dict[str, any]:
    """
    Get severity, category, and remediation for a signal ID.
    
    Args:
        signal_id: The signal identifier (e.g., "http_header_hsts_missing")
    
    Returns:
        Dict with keys: severity, category, remediation
        Returns safe defaults if signal not found in registry.
    """
    registry = _load_registry()
    signals = registry.get("signals", {})
    
    # Direct lookup
    if signal_id in signals:
        info = signals[signal_id]
        return {
            "severity": info.get("severity", "low"),
            "category": info.get("category", "software"),
            "remediation": info.get("remediation", "Review and address this security finding."),
        }
    
    # Pattern matching for wildcards (e.g., "cve_*", "github_leak_*")
    for pattern, info in signals.items():
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            if signal_id.startswith(prefix):
                return {
                    "severity": info.get("severity", "low"),
                    "category": info.get("category", "software"),
                    "remediation": info.get("remediation", "Review and address this security finding."),
                }
    
    # Safe defaults if not found
    return {
        "severity": "low",
        "category": "software",
        "remediation": "Review and address this security finding.",
    }


def get_signal_severity(signal_id: str) -> Severity:
    """Get severity for a signal ID, with safe default."""
    info = get_signal_info(signal_id)
    severity_str = info.get("severity", "low")
    # Validate it's a valid Severity
    if severity_str in ("low", "medium", "high", "critical"):
        return severity_str  # type: ignore
    return "low"


def get_signal_category(signal_id: str) -> Category:
    """Get category for a signal ID, with safe default."""
    info = get_signal_info(signal_id)
    category_str = info.get("category", "software")
    # Validate it's a valid Category
    if category_str in ("network", "software", "data_exposure", "ai_integration"):
        return category_str  # type: ignore
    return "software"


def get_signal_remediation(signal_id: str) -> str:
    """Get remediation guidance for a signal ID."""
    info = get_signal_info(signal_id)
    return info.get("remediation", "Review and address this security finding.")


def reload_registry() -> None:
    """Force reload of the registry (useful for testing or hot-reload scenarios)."""
    global _registry_cache
    _registry_cache = None
    _load_registry()


