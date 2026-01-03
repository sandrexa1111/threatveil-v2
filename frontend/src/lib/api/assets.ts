/**
 * Asset Management API
 * 
 * Frontend API client for asset CRUD operations.
 */
import type {
    Asset,
    AssetCreate,
    AssetUpdate,
    AssetListResponse,
    AssetWithRisk,
    AssetType,
    AssetStatus
} from '@/lib/types';

const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

// =============================================================================
// Asset CRUD Operations
// =============================================================================

export interface AssetFilters {
    type?: AssetType;
    status?: AssetStatus;
    page?: number;
    pageSize?: number;
}

/**
 * List assets for an organization with optional filters.
 */
export async function getAssets(
    orgId: string,
    filters?: AssetFilters
): Promise<AssetListResponse> {
    const params = new URLSearchParams();

    if (filters?.type) params.set('asset_type', filters.type);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.pageSize) params.set('page_size', String(filters.pageSize));

    const queryString = params.toString();
    const url = `${baseUrl}/api/v1/org/${orgId}/assets${queryString ? `?${queryString}` : ''}`;

    const res = await fetch(url);
    if (!res.ok) {
        if (res.status === 404) {
            return { assets: [], total: 0, page: 1, page_size: 20, has_more: false };
        }
        throw new Error('Failed to fetch assets');
    }
    return res.json();
}

/**
 * Get a single asset with risk information.
 */
export async function getAsset(
    orgId: string,
    assetId: string
): Promise<AssetWithRisk> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets/${assetId}`);
    if (!res.ok) {
        throw new Error('Asset not found');
    }
    return res.json();
}

/**
 * Create a new asset.
 */
export async function createAsset(
    orgId: string,
    asset: AssetCreate
): Promise<Asset> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(asset),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to create asset');
    }
    return res.json();
}

/**
 * Update an existing asset.
 */
export async function updateAsset(
    orgId: string,
    assetId: string,
    updates: AssetUpdate
): Promise<AssetWithRisk> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets/${assetId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to update asset');
    }
    return res.json();
}

/**
 * Delete an asset (soft delete by default).
 */
export async function deleteAsset(
    orgId: string,
    assetId: string,
    hardDelete: boolean = false
): Promise<{ message: string }> {
    const res = await fetch(
        `${baseUrl}/api/v1/org/${orgId}/assets/${assetId}?hard_delete=${hardDelete}`,
        { method: 'DELETE' }
    );

    if (!res.ok) {
        throw new Error('Failed to delete asset');
    }
    return res.json();
}

// =============================================================================
// Asset Scanning
// =============================================================================

/**
 * Trigger a manual scan for an asset.
 */
export async function triggerAssetScan(
    orgId: string,
    assetId: string
): Promise<{ message: string; scan_id?: string }> {
    const res = await fetch(
        `${baseUrl}/api/v1/org/${orgId}/assets/${assetId}/scan`,
        { method: 'POST' }
    );

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to trigger scan');
    }
    return res.json();
}

/**
 * Get asset counts grouped by type.
 */
export async function getAssetsByType(
    orgId: string
): Promise<Record<string, number>> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/assets/by-type`);
    if (!res.ok) {
        return {};
    }
    return res.json();
}

// =============================================================================
// Organization Overview
// =============================================================================

import type { OrgOverview } from '@/lib/types';

/**
 * Get organization overview for executive dashboard.
 */
export async function getOrgOverview(orgId: string): Promise<OrgOverview> {
    const res = await fetch(`${baseUrl}/api/v1/org/${orgId}/overview`);
    if (!res.ok) {
        if (res.status === 404) {
            // Return default for new orgs
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
