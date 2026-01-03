"""
Phase 1 Signal Core Schemas

Pydantic schemas for the canonical Signal and Asset models.
These schemas match the database models and are used for API validation.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# =============================================================================
# Type Definitions (Extended for Phase 2)
# =============================================================================

# Original types (backward compatible)
Severity = Literal["low", "medium", "high", "critical"]
Category = Literal["infrastructure", "software", "data", "identity", "ai"]
SignalType = Literal["http", "tls", "dns", "ct", "cve", "github", "otx", "ai_guard", "config", "secret", "network"]

# Phase 2: Extended asset types
AssetTypeEnum = Literal["domain", "github_org", "cloud_account", "saas_vendor"]
ScanFrequencyEnum = Literal["daily", "weekly", "monthly", "manual"]
AssetStatusEnum = Literal["active", "paused", "deleted"]
PlanEnum = Literal["free", "pro", "enterprise"]
RoleEnum = Literal["owner", "security_lead", "viewer"]
DecisionStatusEnum = Literal["pending", "accepted", "in_progress", "resolved", "verified", "rejected"]
AssetPriorityEnum = Literal["critical", "high", "normal", "low"]

# Legacy type kept for backward compatibility
AssetType = Literal["domain", "repository", "ai_agent", "bucket", "ip", "saas_integration"]

# Legacy category type for backward compatibility
LegacyCategory = Literal["network", "software", "data_exposure", "ai_integration"]


# =============================================================================
# Evidence Envelope (Standardized evidence structure)
# =============================================================================

class EvidenceEnvelope(BaseModel):
    """
    Standardized evidence structure for signals.
    This envelope provides all context needed for AI grounding and debugging.
    """
    source_service: str = Field(..., description="Service that generated this evidence")
    observed_at: datetime = Field(..., description="When the evidence was observed")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw data from the source")
    external_refs: List[str] = Field(default_factory=list, description="External reference URLs")
    detection_method: str = Field("rule", description="How this was detected: 'rule' | 'ml' | 'manual'")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence score 0-1")
    notes_for_ai: Optional[str] = Field(None, description="Context notes for AI processing")


# =============================================================================
# Asset Schemas (Phase 2 Extended)
# =============================================================================

class AssetBase(BaseModel):
    """Base asset fields."""
    type: str = Field(..., description="Asset type: domain, github_org, cloud_account, saas_vendor")
    name: str = Field(..., description="Asset name/identifier")
    external_id: Optional[str] = Field(None, description="External ID: AWS Account ID, Azure Tenant, etc.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    risk_tags: List[str] = Field(default_factory=list, description="Risk classification tags")


class AssetCreate(BaseModel):
    """Schema for creating a new asset."""
    type: str = Field(..., description="Asset type: domain, github_org, cloud_account, saas_vendor")
    name: str = Field(..., description="Asset name/identifier")
    external_id: Optional[str] = Field(None, description="External ID (AWS Account ID, Azure Tenant, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    risk_tags: List[str] = Field(default_factory=list, description="Risk classification tags")
    risk_weight: float = Field(1.0, ge=0.1, le=2.0, description="Risk weighting for org aggregation")
    scan_frequency: str = Field("weekly", description="Scan frequency: daily, weekly, monthly, manual")
    owner_email: Optional[str] = Field(None, description="Owner/responsible party email")
    priority: AssetPriorityEnum = Field("normal", description="Asset priority: critical, high, normal, low")


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: Optional[str] = None
    external_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    risk_tags: Optional[List[str]] = None
    risk_weight: Optional[float] = Field(None, ge=0.1, le=2.0)
    scan_frequency: Optional[str] = None
    status: Optional[str] = None
    owner_email: Optional[str] = None
    priority: Optional[AssetPriorityEnum] = None


class AssetRead(BaseModel):
    """Schema for reading an asset with all fields."""
    id: str
    org_id: str
    type: str
    name: str
    external_id: Optional[str] = None
    properties: Dict[str, Any] = {}
    risk_tags: List[str] = []
    risk_weight: float = 1.0
    scan_frequency: str = "weekly"
    last_scan_at: Optional[datetime] = None
    next_scan_at: Optional[datetime] = None
    last_risk_score: Optional[int] = None
    status: str = "active"
    owner_email: Optional[str] = None
    priority: str = "normal"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AssetWithRisk(AssetRead):
    """Asset with computed risk information."""
    current_risk_score: Optional[int] = None
    risk_trend: Optional[int] = None
    signal_count: int = 0


class AssetSummary(BaseModel):
    """Minimal asset info for embedding in signal responses."""
    id: str
    type: str
    name: str


class AssetListResponse(BaseModel):
    """Paginated asset list response."""
    assets: List[AssetRead]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# Signal Schemas (Canonical)
# =============================================================================

class SignalBase(BaseModel):
    """Base signal fields."""
    source: str = Field(..., description="Signal source: threatveil_external, github, otx, etc.")
    type: str = Field(..., description="Signal type: cve, config, network, secret, etc.")
    severity: Severity = Field(..., description="Signal severity")
    category: str = Field(..., description="Signal category: infrastructure, software, data, identity, ai")
    title: str = Field(..., description="Short signal title")
    detail: str = Field(..., description="Detailed description")
    evidence: EvidenceEnvelope = Field(..., description="Evidence envelope")


class SignalCreate(SignalBase):
    """Schema for creating a new signal."""
    org_id: str = Field(..., description="Organization ID")
    scan_id: Optional[str] = Field(None, description="Associated scan ID")
    asset_id: Optional[str] = Field(None, description="Associated asset ID")


class SignalRead(SignalBase):
    """Schema for reading a signal."""
    id: str
    org_id: str
    scan_id: Optional[str]
    asset_id: Optional[str]
    created_at: datetime
    asset: Optional[AssetSummary] = None
    
    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    """Paginated signal list response."""
    signals: List[SignalRead]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# Organization Schemas
# =============================================================================

class OrganizationBase(BaseModel):
    """Base organization fields."""
    name: Optional[str] = None
    primary_domain: str


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationRead(OrganizationBase):
    """Schema for reading an organization."""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrgSummary(BaseModel):
    """
    Organization summary response.
    Used for the /org/{org_id}/summary endpoint.
    """
    org_id: str
    total_signals: int
    signals_by_severity: Dict[str, int]
    signals_by_category: Dict[str, int]
    total_assets: int
    last_scan_at: Optional[datetime]
    top_high_severity_signals: List["SignalRead"]


class EnhancedOrgSummary(OrgSummary):
    """
    Enhanced organization summary with additional fields for dashboard.
    """
    total_scans: int = 0
    risk_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Sparkline data for last 7 scans")
    categories_heatmap: Dict[str, int] = Field(default_factory=dict, description="Signal counts by category")
    ai_exposure_level: str = Field("low", description="Organization AI exposure: low, moderate, high")
    top_recurring_risks: List["SignalRead"] = Field(default_factory=list, description="Top 3 recurring risks")


class DailyBriefResponse(BaseModel):
    """
    Daily security brief response (Phase 2 placeholder).
    """
    top_signals: List["SignalRead"] = Field(default_factory=list, description="Top priority signals")
    top_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    risk_delta: float = Field(0.0, description="Risk change since last brief")
    ai_exposure: str = Field("low", description="Current AI exposure level")
    attack_path_summary: str = Field("Attack path analysis coming in Phase 2", description="Attack path summary")
    last_scan_id: Optional[str] = Field(None, description="Most recent scan ID")


# =============================================================================
# Horizon Schemas (Phase 2 Extended)
# =============================================================================

class DecisionSummary(BaseModel):
    """Compact decision summary for Horizon dashboard."""
    id: str
    title: str
    effort_estimate: str
    estimated_risk_reduction: int
    priority: int
    status: DecisionStatusEnum
    business_impact: Optional[str] = None
    confidence_score: float = 0.8
    asset_name: Optional[str] = None
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verification_scan_id: Optional[str] = None


class AIPosture(BaseModel):
    """AI exposure posture summary."""
    score: int = Field(0, ge=0, le=100, description="AI risk score 0-100")
    trend: int = Field(0, description="Change from previous period")
    status: Literal["clean", "warning", "critical"] = Field("clean", description="Overall AI posture status")


class OrgOverview(BaseModel):
    """
    Organization-level overview for executive dashboard.
    Aggregates risk across all assets with weighted scoring.
    """
    org_id: str
    org_name: Optional[str] = None
    total_risk_score: int = Field(0, ge=0, le=100, description="Weighted aggregate risk score")
    risk_trend_30d: int = Field(0, description="Risk change over 30 days")
    risk_trend_60d: int = Field(0, description="Risk change over 60 days")
    risk_trend_90d: int = Field(0, description="Risk change over 90 days")
    top_risky_assets: List["AssetWithRisk"] = Field(default_factory=list, description="Top 3 risky assets")
    ai_posture: AIPosture = Field(default_factory=AIPosture)
    unresolved_decisions_count: int = Field(0)
    decisions_by_status: Dict[str, int] = Field(default_factory=dict, description="Count of decisions by status")
    decisions_this_week: List[DecisionSummary] = Field(default_factory=list)
    assets_by_type: Dict[str, int] = Field(default_factory=dict)
    total_assets: int = 0
    total_scans_this_month: int = 0
    scans_limit: int = 10
    plan: str = "free"
    last_updated: Optional[datetime] = None
    next_action: str = Field("", description="Recommended next action for the user")


class HorizonResponse(BaseModel):
    """
    Organization-level Horizon dashboard response.
    Aggregates security posture across all scans for an org.
    """
    current_risk_score: int = Field(0, ge=0, le=100, description="Current aggregate risk score")
    risk_trend: int = Field(0, description="Risk score change from previous week")
    top_decisions: List[DecisionSummary] = Field(default_factory=list, description="Top pending decisions")
    unresolved_critical_signals: int = Field(0, ge=0, description="Count of critical/high severity signals")
    ai_posture: AIPosture = Field(default_factory=AIPosture, description="AI exposure summary")
    last_updated: Optional[datetime] = Field(None, description="When data was last updated")
    assets_summary: List["AssetRiskSummary"] = Field(default_factory=list, description="Per-asset risk breakdown")


class DecisionImpact(BaseModel):
    """Impact of a resolved decision with evidence."""
    id: str
    title: str
    risk_delta_points: int = Field(0, description="Actual risk reduction (before - after)")
    evidence_signal_ids: List[str] = Field(default_factory=list, description="Related signal IDs")
    asset_id: Optional[str] = Field(None, description="Associated asset ID")
    asset_name: Optional[str] = Field(None, description="Associated asset name for display")


class AssetRiskSummary(BaseModel):
    """Per-asset risk summary for Horizon dashboard."""
    asset_id: str
    asset_type: str = Field(..., description="Asset type: domain, repo, etc.")
    name: str
    risk_score: int = Field(0, ge=0, le=100)
    trend: int = Field(0, description="Risk change from previous scan")


class WeeklyBriefResponse(BaseModel):
    """
    Weekly security brief response.
    Deterministic summary of org security posture with optional AI explanation.
    """
    headline: str = Field(..., description="Main headline summarizing the week")
    top_changes: List[str] = Field(default_factory=list, description="Key changes from the past week")
    top_3_actions: List[DecisionSummary] = Field(default_factory=list, description="Top 3 priority actions")
    ai_exposure_summary: str = Field("No AI exposure detected", description="AI exposure summary text")
    confidence_level: Literal["low", "medium", "high"] = Field("medium", description="Confidence in the brief")
    explanation: Optional[str] = Field(None, description="Optional AI-generated plain English explanation")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When brief was generated")
    decision_impacts: List[DecisionImpact] = Field(default_factory=list, description="Impact of resolved decisions")


class SendBriefRequest(BaseModel):
    """Request body for sending weekly brief via email."""
    to: str = Field(..., description="Email address to send to")
    include_explanation: bool = Field(True, description="Include AI-generated explanation")


class SendBriefResponse(BaseModel):
    """Response from sending weekly brief."""
    message_id: str = Field(..., description="Email message ID from Resend")
    status: str = Field("sent", description="Send status")


# =============================================================================
# Legacy Schemas (Backward Compatible)
# =============================================================================

class Evidence(BaseModel):
    """Legacy evidence schema for backward compatibility."""
    source: str
    observed_at: datetime
    url: Optional[HttpUrl] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class Signal(BaseModel):
    """Legacy signal schema for backward compatibility with existing scan responses."""
    id: str
    type: SignalType
    detail: str
    severity: Severity
    category: LegacyCategory
    evidence: Evidence


class CategoryScore(BaseModel):
    """Category score for risk scoring."""
    score: int
    weight: float
    severity: Severity


class ScanResult(BaseModel):
    """Scan result response (backward compatible)."""
    id: str
    domain: str
    github_org: Optional[str]
    risk_score: int = Field(ge=0, le=100)
    categories: Dict[LegacyCategory, CategoryScore]
    signals: List[Signal]
    summary: str
    breach_likelihood_30d: float = Field(ge=0.0, le=1.0)
    breach_likelihood_90d: float = Field(ge=0.0, le=1.0)
    created_at: datetime


# =============================================================================
# Request/Response Schemas
# =============================================================================

def _validate_domain(domain: str) -> str:
    """Validate domain: reject IPs, URLs, and ensure it's a bare domain."""
    domain = domain.strip().lower()
    
    if not domain:
        raise ValueError("Domain is required")
    
    if domain.startswith(("http://", "https://", "ftp://", "//")):
        raise ValueError("Please provide a bare domain (e.g., example.com), not a URL")
    
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
    if re.match(ipv4_pattern, domain) or re.match(ipv6_pattern, domain):
        raise ValueError("IP addresses are not supported. Please provide a domain name")
    
    domain_pattern = r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*\.[a-z]{2,}$"
    if not re.match(domain_pattern, domain):
        raise ValueError("Invalid domain format. Use a valid domain like example.com")
    
    if domain in ("localhost", "local", "test"):
        raise ValueError("Localhost and test domains are not supported")
    
    return domain


def _validate_github_org(org: Optional[str]) -> Optional[str]:
    """Validate GitHub org: only alphanumeric and hyphens, reasonable length."""
    if not org:
        return None
    
    org = org.strip()
    
    if not re.match(r"^[A-Za-z0-9-]+$", org):
        raise ValueError("GitHub org can only contain letters, numbers, and hyphens")
    
    if len(org) > 50:
        raise ValueError("GitHub org name must be 50 characters or less")
    
    if len(org) < 1:
        return None
    
    return org


class ScanRequest(BaseModel):
    """Scan request payload."""
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
    """Scan response wrapper."""
    result: ScanResult


class ReportRequest(BaseModel):
    """Report generation request."""
    scan: ScanResult


class ChatRequest(BaseModel):
    """Chat API request."""
    prompt: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat API response."""
    message: str


class AgentResponse(BaseModel):
    """Generic agent response."""
    ok: bool


class SignalQueryParams(BaseModel):
    """Query parameters for signal filtering."""
    severity: Optional[Severity] = None
    category: Optional[str] = None
    asset_id: Optional[str] = None
    source: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# =============================================================================
# Phase 2.3: Type Definitions
# =============================================================================

VerificationResultEnum = Literal["pass", "fail", "unknown"]
ConnectorProviderEnum = Literal["github_app", "slack", "google_workspace", "jira", "notion"]
AIAssetTypeEnum = Literal["model_provider", "agent_framework", "prompt_repo", "vector_db", "automation_tool", "dataset"]
WebhookEventEnum = Literal["weekly_brief.generated", "decision.created", "decision.verified", "risk.score_changed"]


# =============================================================================
# Phase 2.3: Verification Schemas
# =============================================================================

class VerificationRunCreate(BaseModel):
    """Create a new verification run."""
    decision_id: str


class VerificationRunResponse(BaseModel):
    """Response for a verification run."""
    id: str
    decision_id: str
    result: VerificationResultEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VerificationDetailResponse(BaseModel):
    """Detailed verification information for a decision."""
    decision_id: str
    latest_run: Optional[VerificationRunResponse] = None
    evidence_before: Dict[str, Any] = Field(default_factory=dict)
    evidence_after: Optional[Dict[str, Any]] = None
    confidence_explanation: str = ""
    all_runs_count: int = 0


class DecisionEvidenceRead(BaseModel):
    """Evidence record for a decision."""
    id: str
    decision_id: str
    scan_id: Optional[str] = None
    type: str  # 'before' | 'after' | 'diff'
    payload: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Phase 2.3: Connector Schemas
# =============================================================================

class ConnectorCreate(BaseModel):
    """Schema for creating a connector."""
    provider: str = Field(..., description="Connector provider: github_app, slack, etc.")
    name: Optional[str] = Field(None, description="User-friendly display name")
    credentials: Dict[str, str] = Field(..., description="Provider credentials (will be encrypted)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific configuration")
    scopes: List[str] = Field(default_factory=list, description="Requested OAuth scopes")


class ConnectorUpdate(BaseModel):
    """Schema for updating a connector."""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ConnectorRead(BaseModel):
    """Schema for reading a connector (credentials never exposed)."""
    id: str
    org_id: str
    provider: str
    name: Optional[str] = None
    status: str
    scopes: List[str] = []
    config: Dict[str, Any] = Field(default_factory=dict)
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectorListResponse(BaseModel):
    """List of connectors."""
    connectors: List[ConnectorRead]
    total: int


class ConnectorSyncRequest(BaseModel):
    """Request to trigger a connector sync."""
    connector_id: Optional[str] = Field(None, description="Specific connector to sync, or all if None")


class ConnectorSyncResponse(BaseModel):
    """Response from connector sync."""
    synced_connectors: List[str]
    assets_created: int
    signals_created: int
    errors: List[str] = Field(default_factory=list)


# =============================================================================
# Phase 2.3: AI Asset Schemas
# =============================================================================

class AIAssetCreate(BaseModel):
    """Schema for creating an AI asset."""
    type: str = Field(..., description="AI asset type")
    name: str = Field(..., description="Asset name/identifier")
    evidence: Dict[str, Any] = Field(default_factory=dict)
    risk_tags: List[str] = Field(default_factory=list)
    source: str = Field("manual", description="Detection source")
    repository: Optional[str] = None
    file_path: Optional[str] = None


class AIAssetRead(BaseModel):
    """Schema for reading an AI asset."""
    id: str
    org_id: str
    type: str
    name: str
    evidence: Dict[str, Any]
    risk_tags: List[str]
    source: str
    repository: Optional[str] = None
    file_path: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class AIAssetListResponse(BaseModel):
    """Paginated AI asset list."""
    assets: List[AIAssetRead]
    total: int
    page: int
    page_size: int
    has_more: bool


class AIGovernanceResponse(BaseModel):
    """AI Governance dashboard response."""
    ai_posture_score: int = Field(0, ge=0, le=100, description="AI posture score 0-100")
    ai_posture_status: Literal["clean", "warning", "critical"] = Field("clean")
    ai_posture_trend: int = Field(0, description="Score change from previous period")
    assets_by_type: Dict[str, int] = Field(default_factory=dict)
    total_ai_assets: int = 0
    top_ai_risks: List["SignalRead"] = Field(default_factory=list)
    ai_decisions_this_week: List["DecisionSummary"] = Field(default_factory=list)
    last_updated: Optional[datetime] = None


# =============================================================================
# Phase 2.3: Webhook Schemas
# =============================================================================

class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""
    name: Optional[str] = Field(None, description="User-friendly name")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Event types to subscribe to")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    enabled: bool = Field(True)


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None


class WebhookRead(BaseModel):
    """Schema for reading a webhook."""
    id: str
    org_id: str
    name: Optional[str] = None
    url: str
    events: List[str]
    headers: Dict[str, str] = Field(default_factory=dict)
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """List of webhooks."""
    webhooks: List[WebhookRead]
    total: int


class WebhookTestRequest(BaseModel):
    """Request to test a webhook."""
    webhook_id: str


class WebhookTestResponse(BaseModel):
    """Response from webhook test."""
    success: bool
    status_code: Optional[int] = None
    message: str


class WebhookDeliveryRead(BaseModel):
    """Schema for reading a webhook delivery."""
    id: str
    webhook_id: str
    event_type: str
    status: str
    attempts: int
    response_code: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class N8nTemplateResponse(BaseModel):
    """n8n workflow template export."""
    name: str
    workflow: Dict[str, Any]
    description: str
