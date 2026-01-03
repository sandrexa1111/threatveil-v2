'use client';

import { useEffect, useState, useCallback } from 'react';
import { Loader2, Globe, Github, Cloud, Package, Filter } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AddAssetModal } from '@/components/AddAssetModal';
import { AssetCard } from '@/components/AssetCard';
import { getAssets, createAsset, updateAsset, deleteAsset, triggerAssetScan } from '@/lib/api/assets';
import type { Asset, AssetCreate, AssetType, ScanFrequency } from '@/lib/types';

// Demo org ID - in production this would come from auth context
const ORG_ID = 'demo-org';

const assetTypeCounts: Record<AssetType, { icon: React.ReactNode; label: string }> = {
    domain: { icon: <Globe className="h-4 w-4" />, label: 'Domains' },
    github_org: { icon: <Github className="h-4 w-4" />, label: 'GitHub Orgs' },
    cloud_account: { icon: <Cloud className="h-4 w-4" />, label: 'Cloud Accounts' },
    saas_vendor: { icon: <Package className="h-4 w-4" />, label: 'SaaS Vendors' },
};

export default function AssetsPage() {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [typeFilter, setTypeFilter] = useState<AssetType | 'all'>('all');
    const [isUpdating, setIsUpdating] = useState(false);

    const fetchAssets = useCallback(async () => {
        try {
            const response = await getAssets(ORG_ID, {
                type: typeFilter === 'all' ? undefined : typeFilter,
                status: 'active',
            });
            setAssets(response.assets);
            setError(null);
        } catch (err) {
            setError('Failed to load assets');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [typeFilter]);

    useEffect(() => {
        fetchAssets();
    }, [fetchAssets]);

    const handleAddAsset = async (asset: AssetCreate) => {
        await createAsset(ORG_ID, asset);
        await fetchAssets();
    };

    const handleUpdateFrequency = async (assetId: string, frequency: ScanFrequency) => {
        setIsUpdating(true);
        try {
            await updateAsset(ORG_ID, assetId, { scan_frequency: frequency });
            await fetchAssets();
        } finally {
            setIsUpdating(false);
        }
    };

    const handleTriggerScan = async (assetId: string) => {
        await triggerAssetScan(ORG_ID, assetId);
        await fetchAssets();
    };

    const handleDeleteAsset = async (assetId: string) => {
        await deleteAsset(ORG_ID, assetId);
        await fetchAssets();
    };

    // Count assets by type
    const assetCounts = assets.reduce((acc, asset) => {
        acc[asset.type] = (acc[asset.type] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    if (loading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0B0F19] to-[#111827]">
            <div className="mx-auto max-w-7xl space-y-6 px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">Assets</h1>
                        <p className="text-slate-400 mt-1">Manage your protected assets and scan schedules</p>
                    </div>
                    <AddAssetModal onAdd={handleAddAsset} />
                </div>

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                    {(Object.entries(assetTypeCounts) as [AssetType, { icon: React.ReactNode; label: string }][]).map(([type, { icon, label }]) => (
                        <Card key={type} className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-slate-400">
                                        {icon}
                                        <span className="text-sm">{label}</span>
                                    </div>
                                    <span className="text-2xl font-bold text-white">{assetCounts[type] || 0}</span>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Filter Bar */}
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-slate-400">
                        <Filter className="h-4 w-4" />
                        <span className="text-sm">Filter by type:</span>
                    </div>
                    <Select value={typeFilter} onValueChange={(v: string) => setTypeFilter(v as AssetType | 'all')}>
                        <SelectTrigger className="w-[180px] bg-slate-800 border-slate-700 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="all" className="text-white hover:bg-slate-700">All Types</SelectItem>
                            <SelectItem value="domain" className="text-white hover:bg-slate-700">Domains</SelectItem>
                            <SelectItem value="github_org" className="text-white hover:bg-slate-700">GitHub Orgs</SelectItem>
                            <SelectItem value="cloud_account" className="text-white hover:bg-slate-700">Cloud Accounts</SelectItem>
                            <SelectItem value="saas_vendor" className="text-white hover:bg-slate-700">SaaS Vendors</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                        {error}
                    </div>
                )}

                {/* Assets Grid */}
                {assets.length === 0 ? (
                    <Card className="border-slate-800 bg-slate-900/50">
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <Globe className="h-12 w-12 text-slate-600 mb-4" />
                            <h3 className="text-lg font-medium text-white mb-2">No assets yet</h3>
                            <p className="text-slate-400 text-center max-w-sm mb-6">
                                Add your first asset to start monitoring. Assets can be domains, GitHub organizations, cloud accounts, or SaaS vendors.
                            </p>
                            <AddAssetModal onAdd={handleAddAsset} />
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {assets.map((asset) => (
                            <AssetCard
                                key={asset.id}
                                asset={asset}
                                onUpdateFrequency={handleUpdateFrequency}
                                onTriggerScan={handleTriggerScan}
                                onDelete={handleDeleteAsset}
                                isUpdating={isUpdating}
                            />
                        ))}
                    </div>
                )}

                {/* Info Card */}
                <Card className="border-slate-800 bg-slate-900/30">
                    <CardHeader>
                        <CardTitle className="text-white text-sm">About Scan Scheduling</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-3 text-sm">
                            <div className="flex items-start gap-2">
                                <div className="w-2 h-2 rounded-full bg-red-500 mt-1.5" />
                                <div>
                                    <p className="font-medium text-white">Daily</p>
                                    <p className="text-slate-400">For critical, internet-facing assets</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-2">
                                <div className="w-2 h-2 rounded-full bg-amber-500 mt-1.5" />
                                <div>
                                    <p className="font-medium text-white">Weekly</p>
                                    <p className="text-slate-400">Recommended default for most assets</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5" />
                                <div>
                                    <p className="font-medium text-white">Monthly</p>
                                    <p className="text-slate-400">For low-risk, internal-only assets</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
