import { ScanRequestSchema } from '@/schemas/scan';
import {
    ScanResult, ScanAIResult, DecisionListResponse, SecurityDecision, DecisionStatus,
    UpdateStatusResponse, HorizonData, WeeklyBrief, OrgOverview, AISecurityResponse,
    AssetRiskHistoryPoint, RecurringSignalGroup, AssetDecision
} from '@/lib/types';
import { scanVendor } from '@/lib/api';

const STORAGE_KEY = 'threatveil_recent_scans';
const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export interface RecentScan {
    id: string;
    domain: string;
    risk_score: number;
    created_at: string;
}

export function getRecentScans(): RecentScan[] {
    if (typeof window === 'undefined') return [];
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.error('Failed to parse recent scans', e);
        return [];
    }
}

export function addRecentScan(scan: ScanResult) {
    if (typeof window === 'undefined') return;
    const recent: RecentScan = {
        id: scan.id,
        domain: scan.domain,
        risk_score: scan.risk_score,
        created_at: scan.created_at,
    };

    const current = getRecentScans();
    // Remove duplicates by ID and limit to 10
    const updated = [recent, ...current.filter(s => s.id !== scan.id)].slice(0, 10);

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

export function removeRecentScan(id: string) {
    if (typeof window === 'undefined') return;
    const current = getRecentScans();
    const updated = current.filter(s => s.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

export async function deleteScan(id: string): Promise<boolean> {
    const res = await fetch(`${baseUrl}/api/v1/scan/${id}`, {
        method: 'DELETE',
    });

    if (res.status === 204) {
        return true;
    }

    if (!res.ok) {
        throw new Error('Failed to delete scan');
    }

    return true;
}

export async function createScan(payload: ScanRequestSchema): Promise<ScanResult> {
    const result = await scanVendor(payload);
    addRecentScan(result);
    return result;
}

export async function getScan(id: string): Promise<ScanResult> {
    const res = await fetch(`${baseUrl}/api/v1/scan/${id}`);
    if (!res.ok) {
        throw new Error('Scan not found');
    }
    const data = await res.json();
    // Backend returns ScanResponse { result: ScanResult }
    return data.result || data;
}

export interface PreviousScanResult {
    previous_score: number | null;
    previous_scan_id: string | null;
    previous_created_at: string | null;
}

export async function getPreviousScan(id: string): Promise<PreviousScanResult> {
    const res = await fetch(`${baseUrl}/api/v1/scan/${id}/previous`);
    if (!res.ok) {
        return { previous_score: null, previous_scan_id: null, previous_created_at: null };
    }
    return res.json();
}

export async function getScanAI(id: string): Promise<ScanAIResult> {
    const res = await fetch(`${baseUrl}/api/v1/scan/${id}/ai`);
    if (!res.ok) {
        if (res.status === 404) {
            throw new Error('AI scan still running...');
        }
        throw new Error('Failed to fetch AI scan results');
    }
    return res.json();
}

// =============================================================================
// Decision API (Weekly Security Loop)
// =============================================================================

/**
 * Get all decisions for a scan.
 * Returns empty list if no decisions exist yet.
 */
export async function getDecisions(scanId: string): Promise<DecisionListResponse> {
    const res = await fetch(`${baseUrl}/api/v1/scans/${scanId}/decisions`);
    if (!res.ok) {
        if (res.status === 404) {
            return {
                decisions: [],
                pending_count: 0,
                accepted_count: 0,
                in_progress_count: 0,
                resolved_count: 0,
                verified_count: 0,
                total_risk_reduction: 0
            };
        }
        throw new Error('Failed to fetch decisions');
    }
    return res.json();
}

/**
 * Generate decisions for a scan.
 * If decisions already exist, returns existing decisions.
 */
export async function generateDecisions(scanId: string): Promise<DecisionListResponse> {
    const res = await fetch(`${baseUrl}/api/v1/scans/${scanId}/decisions`, {
        method: 'POST',
    });
    if (!res.ok) {
        throw new Error('Failed to generate decisions');
    }
    return res.json();
}

/**
 * Update decision status.
 * Returns the updated decision and risk delta (if resolved).
 */
export async function updateDecisionStatus(
    decisionId: string,
    status: DecisionStatus
): Promise<UpdateStatusResponse> {
    const res = await fetch(`${baseUrl}/api/v1/decisions/${decisionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
    });
    if (!res.ok) {
        throw new Error('Failed to update decision status');
    }
    return res.json();
}

// =============================================================================
// Horizon API (Phase 1.2)
// =============================================================================

/**
 * Get Horizon dashboard data for an organization.
 * Aggregates security posture across all scans.
 */
export async function getHorizonData(orgId: string): Promise<HorizonData> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/horizon`);
    if (!res.ok) {
        if (res.status === 404) {
            // Return default/empty data for new orgs
            return {
                current_risk_score: 0,
                risk_trend: 0,
                top_decisions: [],
                unresolved_critical_signals: 0,
                ai_posture: { score: 0, trend: 0, status: 'clean' },
                last_updated: null,
                assets_summary: [],
            };
        }
        throw new Error('Failed to fetch Horizon data');
    }
    return res.json();
}

/**
 * Get weekly security brief for an organization.
 * Returns human-readable summary with optional AI explanation.
 */
export async function getWeeklyBrief(orgId: string, includeExplanation: boolean = true): Promise<WeeklyBrief> {
    const res = await fetch(
        `${baseUrl}/api/v1/org/${orgId}/weekly-brief?include_explanation=${includeExplanation}`
    );
    if (!res.ok) {
        if (res.status === 404) {
            // Return default brief for new orgs
            return {
                headline: 'Welcome to ThreatVeil',
                top_changes: [],
                top_3_actions: [],
                ai_exposure_summary: 'No scans yet',
                confidence_level: 'low',
                explanation: null,
                generated_at: new Date().toISOString(),
                decision_impacts: [],
            };
        }
        throw new Error('Failed to fetch weekly brief');
    }
    return res.json();
}

/**
 * Send weekly brief via email.
 */
export async function sendWeeklyBrief(orgId: string, email: string): Promise<{ message_id: string; status: string }> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/weekly-brief/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to: email,
            include_explanation: true
        }),
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to send email');
    }

    return res.json();
}

// =============================================================================
// Phase 2 API - Operational Security Intelligence
// =============================================================================

import type { RiskTimeline, DecisionImpactDetail } from '@/lib/types';

/**
 * Get risk timeline for an organization.
 * Returns weekly risk score points for the last N weeks.
 */
export async function getRiskTimeline(orgId: string, weeks: number = 12): Promise<RiskTimeline> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/risk-timeline?weeks=${weeks}`);
    if (!res.ok) {
        if (res.status === 404) {
            return { org_id: orgId, points: [], last_updated: null };
        }
        throw new Error('Failed to fetch risk timeline');
    }
    return res.json();
}

/**
 * Get decision impact for a resolved decision.
 * Returns 404 if decision not resolved or impact not computed.
 */
export async function getDecisionImpact(decisionId: string): Promise<DecisionImpactDetail | null> {
    const res = await fetch(`${baseUrl}/api/v1/decisions/${decisionId}/impact`);
    if (!res.ok) {
        if (res.status === 404) {
            return null;
        }
        throw new Error('Failed to fetch decision impact');
    }
    return res.json();
}

// =============================================================================
// Phase 3 API - Organization Overview
// =============================================================================

/**
 * Get organization overview for executive dashboard.
 * Returns aggregated security posture across all assets.
 */
export async function getOrgOverview(orgId: string): Promise<OrgOverview> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/overview`);
    if (!res.ok) {
        if (res.status === 404) {
            return {
                org_id: orgId,
                org_name: null,
                total_risk_score: 0,
                risk_trend_30d: 0,
                risk_trend_90d: 0,
                top_risky_assets: [],
                ai_posture: { score: 0, trend: 0, status: 'clean' },
                unresolved_decisions_count: 0,
                decisions_this_week: [],
                assets_by_type: {},
                total_assets: 0,
                total_scans_this_month: 0,
                scans_limit: 10,
                plan: 'free',
                last_updated: null,
            };
        }
        throw new Error('Failed to fetch organization overview');
    }
    return res.json();
}

// =============================================================================
// Phase 3 API - AI Security Dashboard
// =============================================================================

/**
 * Get AI security posture for an organization.
 * Returns comprehensive AI exposure data.
 */
export async function getAISecurity(orgId: string, weeks: number = 12): Promise<AISecurityResponse> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/ai-security?weeks=${weeks}`);
    if (!res.ok) {
        if (res.status === 404) {
            return {
                org_id: orgId,
                ai_score: 0,
                ai_status: 'clean',
                ai_tools_detected: [],
                agent_frameworks: [],
                exposed_keys_count: 0,
                exposed_keys_timeline: [],
                ai_risk_trend: [],
                explanation: 'No AI exposure detected. Your organization is AI-clean.',
                next_action: 'Continue monitoring for AI tool usage.',
                last_updated: null,
            };
        }
        throw new Error('Failed to fetch AI security data');
    }
    return res.json();
}

// =============================================================================
// Phase 3 API - Asset Detail
// =============================================================================

/**
 * Get risk score history for an asset.
 * Returns the last N scans with risk scores.
 */
export async function getAssetRiskHistory(
    orgId: string,
    assetId: string,
    limit: number = 10
): Promise<AssetRiskHistoryPoint[]> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets/${assetId}/risk-history?limit=${limit}`);
    if (!res.ok) {
        if (res.status === 404) {
            return [];
        }
        throw new Error('Failed to fetch asset risk history');
    }
    const data = await res.json();
    return data.history || [];
}

/**
 * Get recurring signals for an asset.
 * Returns signals grouped by category that appear across multiple scans.
 */
export async function getAssetRecurringSignals(
    orgId: string,
    assetId: string
): Promise<RecurringSignalGroup[]> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets/${assetId}/recurring-signals`);
    if (!res.ok) {
        if (res.status === 404) {
            return [];
        }
        throw new Error('Failed to fetch recurring signals');
    }
    const data = await res.json();
    return data.groups || [];
}

/**
 * Get security decisions linked to an asset.
 * Returns all decisions for scans of this asset.
 */
export async function getAssetDecisions(
    orgId: string,
    assetId: string,
    status?: string
): Promise<AssetDecision[]> {
    const url = new URL(`${baseUrl}/api/v1/org/${orgId}/assets/${assetId}/decisions`);
    if (status) url.searchParams.set('status', status);
    const res = await fetch(url.toString());
    if (!res.ok) {
        if (res.status === 404) {
            return [];
        }
        throw new Error('Failed to fetch asset decisions');
    }
    const data = await res.json();
    return data.decisions || [];
}

