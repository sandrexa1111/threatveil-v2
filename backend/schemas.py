import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


Severity = Literal["low", "medium", "high"]
Category = Literal["network", "software", "data_exposure", "ai_integration"]
SignalType = Literal["http", "tls", "dns", "ct", "cve", "github", "otx", "ai_guard"]


class Evidence(BaseModel):
    source: str
    observed_at: datetime
    url: Optional[HttpUrl] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class Signal(BaseModel):
    id: str
    type: SignalType
    detail: str
    severity: Severity
    category: Category
    evidence: Evidence


class CategoryScore(BaseModel):
    score: int
    weight: float
    severity: Severity


class ScanResult(BaseModel):
    id: str
    domain: str
    github_org: Optional[str]
    risk_score: int = Field(ge=0, le=100)
    categories: Dict[Category, CategoryScore]
    signals: List[Signal]
    summary: str
    breach_likelihood_30d: float = Field(ge=0.0, le=1.0)
    breach_likelihood_90d: float = Field(ge=0.0, le=1.0)
    created_at: datetime


def _validate_domain(domain: str) -> str:
    """Validate domain: reject IPs, URLs, and ensure it's a bare domain."""
    domain = domain.strip().lower()
    
    # Reject empty
    if not domain:
        raise ValueError("Domain is required")
    
    # Reject URLs (http://, https://, etc.)
    if domain.startswith(("http://", "https://", "ftp://", "//")):
        raise ValueError("Please provide a bare domain (e.g., example.com), not a URL")
    
    # Reject IP addresses (IPv4 and IPv6)
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
    if re.match(ipv4_pattern, domain) or re.match(ipv6_pattern, domain):
        raise ValueError("IP addresses are not supported. Please provide a domain name")
    
    # Basic domain format: alphanumeric, dots, hyphens, must have TLD
    domain_pattern = r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*\.[a-z]{2,}$"
    if not re.match(domain_pattern, domain):
        raise ValueError("Invalid domain format. Use a valid domain like example.com")
    
    # Reject localhost and reserved domains
    if domain in ("localhost", "local", "test"):
        raise ValueError("Localhost and test domains are not supported")
    
    return domain


def _validate_github_org(org: Optional[str]) -> Optional[str]:
    """Validate GitHub org: only alphanumeric and hyphens, reasonable length."""
    if not org:
        return None
    
    org = org.strip()
    
    # Allow only [A-Za-z0-9-]
    if not re.match(r"^[A-Za-z0-9-]+$", org):
        raise ValueError("GitHub org can only contain letters, numbers, and hyphens")
    
    # Reasonable length
    if len(org) > 50:
        raise ValueError("GitHub org name must be 50 characters or less")
    
    if len(org) < 1:
        return None
    
    return org


class ScanRequest(BaseModel):
    domain: str = Field(..., description="Domain to scan (e.g., example.com)")
    github_org: Optional[str] = Field(None, description="Optional GitHub organization to scan")
    
    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return _validate_domain(v)
    
    @field_validator("github_org")
    @classmethod
    def validate_github_org(cls, v: Optional[str]) -> Optional[str]:
        return _validate_github_org(v)


class ScanResponse(BaseModel):
    result: ScanResult


class ReportRequest(BaseModel):
    scan: ScanResult


class ChatRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    message: str


class AgentResponse(BaseModel):
    ok: bool
