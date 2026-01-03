"""
Signals Package

Services for creating and managing canonical signals.
"""
from .asset_mapper import (
    get_or_create_domain_asset,
    get_or_create_repo_asset,
    get_or_create_ai_agent_asset,
    add_risk_tags_to_asset,
)
from .signal_normalizer import (
    create_canonical_signal,
    hsts_missing_to_signal,
    missing_csp_to_signal,
    tls_expiry_to_signal,
    tls_weak_to_signal,
    dns_issue_to_signal,
    cve_to_signal,
    otx_pulse_to_signal,
    github_key_leak_to_signal,
    ai_tool_to_signal,
    ai_agent_to_signal,
    service_error_to_signal,
)

__all__ = [
    # Asset mapper
    "get_or_create_domain_asset",
    "get_or_create_repo_asset",
    "get_or_create_ai_agent_asset",
    "add_risk_tags_to_asset",
    # Signal normalizer
    "create_canonical_signal",
    "hsts_missing_to_signal",
    "missing_csp_to_signal",
    "tls_expiry_to_signal",
    "tls_weak_to_signal",
    "dns_issue_to_signal",
    "cve_to_signal",
    "otx_pulse_to_signal",
    "github_key_leak_to_signal",
    "ai_tool_to_signal",
    "ai_agent_to_signal",
    "service_error_to_signal",
]
