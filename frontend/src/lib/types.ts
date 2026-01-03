export type Severity = 'low' | 'medium' | 'high';
export type Category = 'network' | 'software' | 'data_exposure' | 'ai_integration';
export type SignalType = 'http' | 'tls' | 'dns' | 'ct' | 'cve' | 'github' | 'otx' | 'ai_guard';

export interface Evidence {
  source: string;
  observed_at: string;
  url?: string | null;
  raw: Record<string, unknown>;
}

export interface Signal {
  id: string;
  type: SignalType;
  detail: string;
  severity: Severity;
  category: Category;
  evidence: Evidence;
}

export interface CategoryScore {
  score: number;
  weight: number;
  severity: Severity;
}

export interface ScanResult {
  id: string;
  domain: string;
  github_org?: string | null;
  risk_score: number;
  categories: Record<Category, CategoryScore>;
  signals: Signal[];
  summary: string;
  breach_likelihood_30d: number;
  breach_likelihood_90d: number;
  created_at: string;
}

export interface ScanResponse {
  result: ScanResult;
}

export interface ScanAIResult {
  scan_id: string;
  ai_score: number;
  ai_tools_detected: string[];
  ai_agents_detected: string[];
  ai_key_leaks: Array<{
    key_type?: string;
    repository?: string;
    path?: string;
    url?: string;
  }>;
  ai_summary: string;
  created_at: string;
}

// Decision tracking types for Weekly Security Loop (Phase 3 Extended)
export type DecisionStatus = 'pending' | 'accepted' | 'in_progress' | 'resolved' | 'verified';

export interface SecurityDecision {
  id: string;
  scan_id: string;
  action_id: string;
  title: string;
  recommended_fix: string;
  effort_estimate: string;
  estimated_risk_reduction: number;
  priority: number;
  status: DecisionStatus;
  before_score: number | null;
  after_score: number | null;
  business_impact: string | null;
  confidence_score: number;
  confidence_reason: string | null;
  verification_scan_id: string | null;
  created_at: string;
  updated_at: string;
  accepted_at: string | null;
  resolved_at: string | null;
  verified_at: string | null;
}

export interface DecisionListResponse {
  decisions: SecurityDecision[];
  pending_count: number;
  accepted_count: number;
  in_progress_count: number;
  resolved_count: number;
  verified_count: number;
  total_risk_reduction: number;
}

export interface UpdateStatusResponse {
  decision: SecurityDecision;
  risk_delta: number | null;
}

// =============================================================================
// Horizon Types (Phase 1.2)
// =============================================================================

export interface DecisionSummary {
  id: string;
  title: string;
  effort_estimate: string;
  estimated_risk_reduction: number;
  priority: number;
  status: string;
  business_impact?: string | null;
  confidence_score: number;
  asset_name?: string | null;
}

export interface AIPosture {
  score: number;
  trend: number;
  status: 'clean' | 'warning' | 'critical';
}

export interface HorizonData {
  current_risk_score: number;
  risk_trend: number;
  top_decisions: DecisionSummary[];
  unresolved_critical_signals: number;
  ai_posture: AIPosture;
  last_updated: string | null;
  assets_summary: AssetRiskSummary[];
}

export interface WeeklyBrief {
  headline: string;
  top_changes: string[];
  top_3_actions: DecisionSummary[];
  ai_exposure_summary: string;
  confidence_level: 'low' | 'medium' | 'high';
  explanation?: string | null;
  generated_at: string;
  decision_impacts: DecisionImpact[];
}

// =============================================================================
// Phase 1.3 Types
// =============================================================================

export interface DecisionImpact {
  id: string;
  title: string;
  risk_delta_points: number;
  evidence_signal_ids: string[];
  asset_id: string | null;
  asset_name: string | null;
}

export interface AssetRiskSummary {
  asset_id: string;
  asset_type: string;
  name: string;
  risk_score: number;
  trend: number;
}

// =============================================================================
// Phase 2 Types - Operational Security Intelligence
// =============================================================================

export interface RiskTimelinePoint {
  week_start: string;
  risk_score: number;
  ai_score: number | null;
  delta_from_prev: number | null;
}

export interface RiskTimeline {
  org_id: string;
  points: RiskTimelinePoint[];
  last_updated: string | null;
}

export interface DecisionImpactDetail {
  decision_id: string;
  risk_before: number;
  risk_after: number | null;
  delta: number | null;
  confidence: number;
  computed_at: string;
  notes: string | null;
}

// =============================================================================
// Phase 2 Types - Asset Management
// =============================================================================

export type AssetType = 'domain' | 'github_org' | 'cloud_account' | 'saas_vendor';
export type ScanFrequency = 'daily' | 'weekly' | 'monthly' | 'manual';
export type AssetStatus = 'active' | 'paused' | 'deleted';
export type PlanType = 'free' | 'pro' | 'enterprise';
export type UserRole = 'owner' | 'security_lead' | 'viewer';

export interface Asset {
  id: string;
  org_id: string;
  type: AssetType;
  name: string;
  external_id: string | null;
  properties: Record<string, unknown>;
  risk_tags: string[];
  risk_weight: number;
  scan_frequency: ScanFrequency;
  last_scan_at: string | null;
  next_scan_at: string | null;
  last_risk_score: number | null;
  status: AssetStatus;
  owner_email: string | null;
  priority: 'critical' | 'high' | 'normal' | 'low';
  created_at: string;
  updated_at: string;
}

export interface AssetCreate {
  type: AssetType;
  name: string;
  external_id?: string;
  properties?: Record<string, unknown>;
  risk_tags?: string[];
  risk_weight?: number;
  scan_frequency?: ScanFrequency;
}

export interface AssetUpdate {
  name?: string;
  external_id?: string;
  properties?: Record<string, unknown>;
  risk_tags?: string[];
  risk_weight?: number;
  scan_frequency?: ScanFrequency;
  status?: AssetStatus;
  owner_email?: string;
  priority?: 'critical' | 'high' | 'normal' | 'low';
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AssetWithRisk extends Asset {
  current_risk_score: number | null;
  risk_trend: number | null;
  signal_count: number;
}

// =============================================================================
// Phase 2 Types - Organization Overview
// =============================================================================

export interface AIPostureExtended {
  score: number;
  trend: number;
  status: 'clean' | 'warning' | 'critical';
}

export interface OrgOverview {
  org_id: string;
  org_name: string | null;
  total_risk_score: number;
  risk_trend_30d: number;
  risk_trend_90d: number;
  top_risky_assets: AssetWithRisk[];
  ai_posture: AIPostureExtended;
  unresolved_decisions_count: number;
  decisions_this_week: DecisionSummary[];
  assets_by_type: Record<string, number>;
  total_assets: number;
  total_scans_this_month: number;
  scans_limit: number;
  plan: PlanType;
  last_updated: string | null;
}

// =============================================================================
// User & Role Types
// =============================================================================

export interface User {
  id: string;
  org_id: string;
  email: string;
  name: string | null;
  role: UserRole;
  created_at: string;
}

// =============================================================================
// Phase 3 Types - AI Security Dashboard
// =============================================================================

export interface AIToolDetected {
  name: string;
  count: number;
  first_seen: string | null;
  last_seen: string | null;
  is_agent_framework: boolean;
}

export interface ExposedKeyEvent {
  date: string;
  count: number;
  key_types: string[];
}

export interface AIRiskPoint {
  week_start: string;
  ai_score: number;
  delta: number | null;
}

export interface AISecurityResponse {
  org_id: string;
  ai_score: number;
  ai_status: 'clean' | 'warning' | 'critical';
  ai_tools_detected: AIToolDetected[];
  agent_frameworks: string[];
  exposed_keys_count: number;
  exposed_keys_timeline: ExposedKeyEvent[];
  ai_risk_trend: AIRiskPoint[];
  explanation: string;
  next_action: string;
  last_updated: string | null;
}

// =============================================================================
// Phase 3 Types - Asset Detail
// =============================================================================

export interface AssetRiskHistoryPoint {
  scan_id: string;
  risk_score: number;
  created_at: string;
}

export interface RecurringSignalGroup {
  category: string;
  signal_type: string;
  count: number;
  severity: Severity;
  first_seen: string;
  last_seen: string;
  title: string;
}

export interface AssetDecision {
  id: string;
  title: string;
  status: DecisionStatus;
  priority: number;
  effort_estimate: string;
  estimated_risk_reduction: number;
  created_at: string;
  scan_id: string;
}
