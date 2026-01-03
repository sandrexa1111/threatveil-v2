import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .db import Base


# =============================================================================
# Organization (Multi-Tenant Root)
# =============================================================================

class Organization(Base):
    """
    Organization model for multi-tenant support.
    This is the root entity for all tenant-scoped data.
    
    Note: Previously named 'Company' - kept as alias for backward compatibility.
    """
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    primary_domain = Column(String, nullable=False, index=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Productization: Usage limits
    plan = Column(String, default='free', nullable=False)  # 'free' | 'pro' | 'enterprise'
    scans_this_month = Column(Integer, default=0, nullable=False)
    scans_limit = Column(Integer, default=10, nullable=False)  # Free tier limit

    # Relationships - use explicit foreign_keys due to legacy company_id column
    scans = relationship("Scan", back_populates="organization", cascade="all, delete-orphan", foreign_keys="[Scan.org_id]")
    assets = relationship("Asset", back_populates="organization", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


# Backward compatibility alias
Company = Organization


# =============================================================================
# User (Authenticated users tied to an org)
# =============================================================================

class User(Base):
    """
    User model for authenticated users.
    Each user belongs to exactly one organization.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="member")  # 'admin' | 'member' | 'viewer'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    organization = relationship("Organization", back_populates="users")


# =============================================================================
# Asset (Unified representation of scannable entities)
# =============================================================================

class Asset(Base):
    """
    Asset represents any entity that can have security signals:
    - domains, repositories, cloud accounts, SaaS vendors, etc.
    
    Assets are org-scoped and support continuous monitoring via scan schedules.
    
    Asset Types:
    - 'domain': Website domain (existing)
    - 'github_org': GitHub organization (existing)
    - 'cloud_account': AWS/Azure/GCP account (metadata only)
    - 'saas_vendor': Third-party SaaS service
    
    Priority levels:
    - 'critical': Business-critical assets that require immediate attention
    - 'high': Important assets with elevated risk weight
    - 'normal': Standard priority (default)
    - 'low': Lower priority assets
    """
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # 'domain' | 'github_org' | 'cloud_account' | 'saas_vendor'
    name = Column(String, nullable=False)  # e.g. "threatveil.com" or "my-org"
    external_id = Column(String, nullable=True)  # AWS Account ID, Azure Tenant ID, GCP Project ID
    properties = Column(JSON, nullable=False, default=dict)  # Additional metadata
    risk_tags = Column(JSON, nullable=False, default=list)  # e.g. ['internet_exposed', 'contains_pii']
    
    # Ownership and priority (Phase 3)
    owner_email = Column(String, nullable=True)  # Owner/responsible party email
    priority = Column(String, default='normal', nullable=False)  # 'critical' | 'high' | 'normal' | 'low'
    
    # Risk weighting for org-level aggregation
    risk_weight = Column(Float, default=1.0, nullable=False)  # 0.1 - 2.0 multiplier
    
    # Scan scheduling
    scan_frequency = Column(String, default='weekly', nullable=False)  # 'daily' | 'weekly' | 'monthly' | 'manual'
    last_scan_at = Column(DateTime, nullable=True)
    next_scan_at = Column(DateTime, nullable=True)
    last_risk_score = Column(Integer, nullable=True)  # Cached for quick org aggregation
    
    # Status
    status = Column(String, default='active', nullable=False)  # 'active' | 'paused' | 'deleted'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="assets")
    signals = relationship("Signal", back_populates="asset", cascade="all, delete-orphan")
    schedules = relationship("ScanSchedule", back_populates="asset", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_assets_org_type_name", "org_id", "type", "name"),
        Index("idx_assets_next_scan", "next_scan_at", "status"),
        Index("idx_assets_org_priority", "org_id", "priority"),
    )


# =============================================================================
# Signal (Canonical security finding)
# =============================================================================

class Signal(Base):
    """
    Signal represents a canonical security finding or observation.
    
    Signals are the core data model for ThreatVeil's Signal Platform.
    They normalize all security evidence into a single schema.
    
    Evidence envelope structure (in evidence JSONB):
    {
        "source_service": "tls_service",
        "observed_at": "2025-12-05T12:00:00Z",
        "raw": {...},
        "external_refs": ["https://..."],
        "detection_method": "rule",
        "confidence": 0.9,
        "notes_for_ai": "Missing HSTS on main endpoint"
    }
    """
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True, index=True)
    asset_id = Column(String, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Signal classification
    source = Column(String, nullable=False)  # 'threatveil_external' | 'github' | 'otx' | 'nvd' | etc.
    type = Column(String, nullable=False)  # 'cve' | 'config' | 'network' | 'secret' | 'ai_exposure' | etc.
    severity = Column(String, nullable=False)  # 'low' | 'medium' | 'high' | 'critical'
    category = Column(String, nullable=False)  # 'infrastructure' | 'software' | 'data' | 'identity' | 'ai'
    
    # Signal content
    title = Column(String, nullable=False)
    detail = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)  # Structured evidence envelope
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="signals")
    scan = relationship("Scan", back_populates="signals_rel")
    asset = relationship("Asset", back_populates="signals")

    # Indexes for common query patterns
    __table_args__ = (
        Index("idx_signals_org_sev_cat", "org_id", "severity", "category"),
        Index("idx_signals_org_asset", "org_id", "asset_id"),
        Index("idx_signals_org_created", "org_id", "created_at"),
    )


# =============================================================================
# Scan (Scan execution record)
# =============================================================================

class Scan(Base):
    """
    Scan represents a single scan execution.
    
    A scan produces signals and is linked to an organization.
    """
    __tablename__ = "scans"

    id = Column(String, primary_key=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    domain = Column(String, nullable=False, index=True)
    github_org = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=False)
    risk_likelihood_30d = Column(Float, nullable=False)
    risk_likelihood_90d = Column(Float, nullable=False)
    categories_json = Column(JSON, nullable=False)
    signals_json = Column(JSON, nullable=False)  # Legacy: signals stored as JSON for quick retrieval
    summary = Column(Text, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Legacy column - kept for backward compatibility during migration
    company_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="scans", foreign_keys=[org_id])
    scan_ai = relationship("ScanAI", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    signals_rel = relationship("Signal", back_populates="scan", cascade="all, delete-orphan")
    decisions = relationship("SecurityDecision", back_populates="scan", cascade="all, delete-orphan", foreign_keys="[SecurityDecision.scan_id]")

    # Indexes
    __table_args__ = (
        Index("idx_scans_org_created", "org_id", "created_at"),
    )

    @property
    def importance_score(self) -> int:
        """
        Compute scan importance score based on critical/high signals and breach likelihood.
        Returns: 0-100 score indicating scan priority.
        """
        score = 0
        
        # Count signals by severity from signals_json
        if self.signals_json:
            for signal in self.signals_json:
                severity = signal.get("severity", "low")
                if severity == "critical":
                    score += 25
                elif severity == "high":
                    score += 15
                elif severity == "medium":
                    score += 5
                elif severity == "low":
                    score += 1
        
        # Factor in breach likelihood
        if self.risk_likelihood_30d:
            score += int(self.risk_likelihood_30d * 20)
        
        return min(score, 100)


# =============================================================================
# ScanAI (AI-specific scan data)
# =============================================================================

class ScanAI(Base):
    """AI-specific scan data for Horizon features."""
    __tablename__ = "scan_ai"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, unique=True, index=True)
    ai_tools = Column(JSON, nullable=True)  # List of detected AI tools/frameworks
    ai_vendors = Column(JSON, nullable=True)  # List of AI vendors and inferred risk
    ai_keys = Column(JSON, nullable=True)  # Detected AI key leak signals
    ai_score = Column(Integer, nullable=True)  # 0-100 Horizon AI risk score
    ai_summary = Column(Text, nullable=True)  # AI-specific summary
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    scan = relationship("Scan", back_populates="scan_ai")

    @property
    def ai_exposure_level(self) -> str:
        """
        Compute AI exposure level based on ai_score.
        Returns: 'low' (≤20), 'moderate' (21-50), 'high' (>50)
        """
        if self.ai_score is None:
            return "low"
        if self.ai_score <= 20:
            return "low"
        elif self.ai_score <= 50:
            return "moderate"
        return "high"


# =============================================================================
# CacheEntry (Internal caching)
# =============================================================================

class CacheEntry(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)


# =============================================================================
# SecurityDecision (Persisted security decisions with tracking)
# =============================================================================

class SecurityDecision(Base):
    """
    Persisted security decision generated from scan findings.
    
    Decisions are generated deterministically (no LLM) and track:
    - Completion status (pending → accepted → in_progress → resolved → verified)
    - Risk delta (before_score vs after_score)
    - Business impact and confidence for executive communication
    - Verification via subsequent scans
    
    This enables the "Weekly Security Loop" where users can see
    what they fixed and how risk changed.
    
    Status Lifecycle:
    - pending: Decision generated, awaiting action
    - accepted: User acknowledged, planning to address
    - in_progress: User actively working on fix
    - resolved: User marked as complete
    - verified: Subsequent scan confirms the fix worked
    """
    __tablename__ = "security_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Decision details (deterministic, no LLM)
    action_id = Column(String, nullable=False)  # e.g., 'key-rotation', 'patch-cves'
    title = Column(String, nullable=False)
    recommended_fix = Column(Text, nullable=False)
    effort_estimate = Column(String, nullable=False)
    estimated_risk_reduction = Column(Integer, nullable=False)  # percentage
    priority = Column(Integer, nullable=False)  # 1 = highest
    
    # Decision Engine V2: Business language
    business_impact = Column(Text, nullable=True)  # e.g., "Prevents unauthorized AI usage"
    confidence_score = Column(Float, default=0.8, nullable=False)  # 0.0 - 1.0
    confidence_reason = Column(String, nullable=True)  # e.g., "High: Multiple sources confirm"
    
    # Status tracking: pending | accepted | in_progress | resolved | verified
    status = Column(String, nullable=False, default='pending')
    
    # Risk delta (populated on status changes)
    before_score = Column(Integer, nullable=True)  # Risk score when decision created
    after_score = Column(Integer, nullable=True)   # Risk score after resolution
    
    # Verification tracking
    verification_scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Phase 2.3: Verification Engine
    verification_status = Column(String, nullable=True)  # 'pass' | 'fail' | 'unknown'
    verification_notes = Column(Text, nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="decisions", foreign_keys=[scan_id])
    asset = relationship("Asset")
    impact = relationship("DecisionImpact", back_populates="decision", uselist=False, cascade="all, delete-orphan")
    verification_scan = relationship("Scan", foreign_keys=[verification_scan_id])

    # Indexes
    __table_args__ = (
        Index("idx_decisions_scan_status", "scan_id", "status"),
        Index("idx_decisions_org_status", "status"),
    )


# =============================================================================
# DecisionImpact (Phase 2 - Operational Security Intelligence)
# =============================================================================

class DecisionImpact(Base):
    """
    Tracks measured risk reduction when a decision is resolved.
    
    Links a decision to its before/after scans for delta calculation.
    Computed deterministically (no LLM) when a decision transitions to 'resolved'.
    
    Confidence scoring:
    - 1.0: after-scan within 7 days + triggering signal no longer present
    - 0.7: after-scan within 7 days, signal presence unknown
    - 0.4: after-scan older than 7 days
    - 0.2: no after-scan exists
    """
    __tablename__ = "decision_impacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_id = Column(String, ForeignKey("security_decisions.id", ondelete="CASCADE"), nullable=False, unique=True)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)  # before scan
    resolved_scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)  # after scan
    
    risk_before = Column(Integer, nullable=False)  # 0-100
    risk_after = Column(Integer, nullable=True)     # 0-100, null if no after scan
    delta = Column(Integer, nullable=True)          # risk_after - risk_before (negative = good)
    confidence = Column(Float, nullable=False, default=0.2)  # 0.0 - 1.0
    
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # e.g., "insufficient data", "signal still present"
    
    # Relationships
    decision = relationship("SecurityDecision", back_populates="impact")
    before_scan = relationship("Scan", foreign_keys=[scan_id])
    after_scan = relationship("Scan", foreign_keys=[resolved_scan_id])

    # Indexes
    __table_args__ = (
        Index("idx_decision_impacts_org", "org_id"),
        Index("idx_decision_impacts_decision", "decision_id"),
    )


# =============================================================================
# ScanSchedule (Continuous Monitoring)
# =============================================================================

class ScanSchedule(Base):
    """
    Scan schedule for continuous monitoring of assets.
    
    Frequencies:
    - 'daily': Critical assets, runs every 24h
    - 'weekly': Default, runs every 7 days
    - 'monthly': Low-risk assets, runs every 30 days
    """
    __tablename__ = "scan_schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    frequency = Column(String, nullable=False)  # 'daily' | 'weekly' | 'monthly'
    next_run_at = Column(DateTime, nullable=False, index=True)
    last_run_at = Column(DateTime, nullable=True)
    last_scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String, default='active', nullable=False)  # 'active' | 'paused'
    run_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="schedules")
    last_scan = relationship("Scan", foreign_keys=[last_scan_id])

    # Indexes
    __table_args__ = (
        Index("idx_schedules_next_run", "next_run_at", "status"),
        Index("idx_schedules_org_asset", "org_id", "asset_id"),
    )


# =============================================================================
# AuditLog (Productization - Compliance & Tracking)
# =============================================================================

class AuditLog(Base):
    """
    Audit log for tracking important actions.
    
    Used for compliance, debugging, and investor-ready reporting.
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String, nullable=False)  # 'decision_resolved', 'asset_created', 'scan_started'
    resource_type = Column(String, nullable=True)  # 'decision', 'asset', 'scan'
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)  # Additional context
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_audit_org_created", "org_id", "created_at"),
        Index("idx_audit_action", "action"),
    )


# =============================================================================
# ShareableReport (Read-only shareable links)
# =============================================================================

class ShareableReport(Base):
    """
    Shareable read-only report links.
    
    Generates time-limited public access tokens for sharing reports
    with executives, auditors, or external parties.
    """
    __tablename__ = "shareable_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    token = Column(String, nullable=False, unique=True, index=True)  # Public access token
    report_type = Column(String, nullable=False)  # 'horizon', 'scan', 'org_overview'
    resource_id = Column(String, nullable=True)  # Scan ID if type='scan'
    
    expires_at = Column(DateTime, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    max_views = Column(Integer, nullable=True)  # Optional view limit
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_shareable_token", "token"),
        Index("idx_shareable_org", "org_id"),
    )


# =============================================================================
# Phase 2.3: Decision Evidence (Verification Proof)
# =============================================================================

class DecisionEvidence(Base):
    """
    Evidence captured during decision verification.
    
    Stores before/after snapshots of security state for proof of fix.
    Each decision can have multiple evidence records (before, after, diff).
    """
    __tablename__ = "decision_evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String, ForeignKey("security_decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    type = Column(String, nullable=False)  # 'before' | 'after' | 'diff'
    payload = Column(JSON, nullable=False)  # Evidence data (signals, headers, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    decision = relationship("SecurityDecision", backref="evidence_records")
    scan = relationship("Scan")

    __table_args__ = (
        Index("idx_decision_evidence_decision", "decision_id"),
    )


# =============================================================================
# Phase 2.3: Decision Verification Run
# =============================================================================

class DecisionVerificationRun(Base):
    """
    Record of a verification attempt for a decision.
    
    Each run captures:
    - When verification was attempted
    - Result (pass/fail/unknown)
    - Confidence score with tiers
    - Evidence collected during verification
    """
    __tablename__ = "decision_verification_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String, ForeignKey("security_decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(String, nullable=False)  # 'pass' | 'fail' | 'unknown'
    confidence = Column(Float, nullable=False, default=0.2)  # 0.0 - 1.0
    notes = Column(Text, nullable=True)  # Explanation of result
    evidence = Column(JSON, nullable=False, default=dict)  # Verification evidence snapshot
    
    # Relationships
    decision = relationship("SecurityDecision", backref="verification_runs")

    __table_args__ = (
        Index("idx_verification_runs_decision", "decision_id"),
        Index("idx_verification_runs_result", "result"),
    )


# =============================================================================
# Phase 2.3: Connector (External Service Integration)
# =============================================================================

class Connector(Base):
    """
    External service connector for expanded security visibility.
    
    Supports OAuth and token-based integrations:
    - github_app: GitHub organization inventory
    - slack: Webhook delivery for weekly briefs
    - google_workspace: Future expansion
    - jira: Future expansion
    
    Credentials are encrypted at rest using Fernet symmetric encryption.
    """
    __tablename__ = "connectors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # 'github_app' | 'slack' | 'google_workspace' | etc.
    name = Column(String, nullable=True)  # User-friendly display name
    status = Column(String, default='active', nullable=False)  # 'active' | 'paused' | 'error'
    encrypted_credentials = Column(Text, nullable=True)  # Fernet-encrypted JSON credentials
    scopes = Column(JSON, nullable=False, default=list)  # Requested OAuth scopes
    config = Column(JSON, nullable=False, default=dict)  # Provider-specific config (e.g., org name, channel)
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="connectors")

    __table_args__ = (
        Index("idx_connectors_org_provider", "org_id", "provider"),
        Index("idx_connectors_status", "status"),
    )


# =============================================================================
# Phase 2.3: AI Asset (AI Governance Inventory)
# =============================================================================

class AIAsset(Base):
    """
    AI-specific asset discovered from scans or connectors.
    
    Types:
    - model_provider: OpenAI, Anthropic, Google, Cohere, HuggingFace
    - agent_framework: LangChain, LangGraph, CrewAI, AutoGen
    - prompt_repo: Prompt templates, AI config files
    - vector_db: Pinecone, Weaviate, pgvector usage
    - automation_tool: n8n/Zapier AI integrations, MCP servers
    
    AI assets contribute to the AI Posture Score and enable
    AI-specific risk controls and recommendations.
    """
    __tablename__ = "ai_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # Type classification
    name = Column(String, nullable=False)  # Asset name/identifier
    evidence = Column(JSON, nullable=False, default=dict)  # Detection evidence
    risk_tags = Column(JSON, nullable=False, default=list)  # Risk classification tags
    source = Column(String, nullable=False)  # 'github' | 'manual' | 'connector' | 'scan'
    repository = Column(String, nullable=True)  # Source repository if from GitHub
    file_path = Column(String, nullable=True)  # File path where detected
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default='active', nullable=False)  # 'active' | 'archived'
    
    # Relationships
    organization = relationship("Organization", backref="ai_assets")

    __table_args__ = (
        Index("idx_ai_assets_org_type", "org_id", "type"),
        Index("idx_ai_assets_org_name", "org_id", "name"),
    )


# =============================================================================
# Phase 2.3: Webhook (Automation Integration)
# =============================================================================

class Webhook(Base):
    """
    Webhook configuration for automation integrations.
    
    Supports n8n, Zapier, and custom webhook receivers.
    
    Event types:
    - weekly_brief.generated: Weekly brief is ready
    - decision.created: New security decision generated
    - decision.verified: Decision fix has been verified
    - risk.score_changed: Organization risk score changed significantly
    
    Delivery includes HMAC-SHA256 signature for verification.
    """
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=True)  # User-friendly name
    url = Column(String, nullable=False)  # Webhook endpoint URL
    secret = Column(String, nullable=False)  # HMAC signing secret
    events = Column(JSON, nullable=False, default=list)  # List of subscribed event types
    enabled = Column(Boolean, default=True, nullable=False)
    headers = Column(JSON, nullable=False, default=dict)  # Custom headers to include
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="webhooks")

    __table_args__ = (
        Index("idx_webhooks_org", "org_id"),
        Index("idx_webhooks_enabled", "enabled"),
    )


# =============================================================================
# Phase 2.3: Webhook Delivery (Audit Log)
# =============================================================================

class WebhookDelivery(Base):
    """
    Audit log for webhook delivery attempts.
    
    Tracks:
    - Event payload and metadata
    - Delivery status with retry attempts
    - Response from receiver
    """
    __tablename__ = "webhook_deliveries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)  # Event payload sent
    status = Column(String, nullable=False, default='pending')  # 'pending' | 'success' | 'failed'
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    webhook = relationship("Webhook", backref="deliveries")

    __table_args__ = (
        Index("idx_webhook_deliveries_webhook", "webhook_id"),
        Index("idx_webhook_deliveries_status", "status"),
        Index("idx_webhook_deliveries_created", "created_at"),
    )
