'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
    Globe,
    Github,
    Cloud,
    Package,
    Play,
    Trash2,
    Clock,
    AlertTriangle,
    CheckCircle2,
    Loader2
} from 'lucide-react';
import type { Asset, ScanFrequency } from '@/lib/types';

interface AssetCardProps {
    asset: Asset;
    onUpdateFrequency: (assetId: string, frequency: ScanFrequency) => Promise<void>;
    onTriggerScan: (assetId: string) => Promise<void>;
    onDelete: (assetId: string) => Promise<void>;
    isUpdating?: boolean;
}

const assetTypeIcons: Record<string, React.ReactNode> = {
    domain: <Globe className="h-5 w-5 text-blue-400" />,
    github_org: <Github className="h-5 w-5 text-gray-400" />,
    cloud_account: <Cloud className="h-5 w-5 text-amber-400" />,
    saas_vendor: <Package className="h-5 w-5 text-purple-400" />,
};

const assetTypeLabels: Record<string, string> = {
    domain: 'Domain',
    github_org: 'GitHub Org',
    cloud_account: 'Cloud Account',
    saas_vendor: 'SaaS Vendor',
};

function formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function formatRelativeDate(dateStr: string | null): string {
    if (!dateStr) return 'Not scheduled';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();

    if (diff < 0) return 'Overdue';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) return `In ${days} day${days > 1 ? 's' : ''}`;
    if (hours > 0) return `In ${hours} hour${hours > 1 ? 's' : ''}`;
    return 'Soon';
}

function getRiskColor(score: number | null): string {
    if (score === null) return 'bg-slate-500';
    if (score >= 70) return 'bg-red-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-emerald-500';
}

export function AssetCard({
    asset,
    onUpdateFrequency,
    onTriggerScan,
    onDelete,
    isUpdating = false,
}: AssetCardProps) {
    const [isScanning, setIsScanning] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleScan = async () => {
        setIsScanning(true);
        try {
            await onTriggerScan(asset.id);
        } finally {
            setIsScanning(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Are you sure you want to delete ${asset.name}?`)) return;
        setIsDeleting(true);
        try {
            await onDelete(asset.id);
        } finally {
            setIsDeleting(false);
        }
    };

    const isActive = asset.status === 'active';

    return (
        <Card className={`border-slate-800 bg-slate-900/50 backdrop-blur-sm transition-all hover:border-slate-700 ${!isActive ? 'opacity-60' : ''}`}>
            <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                    {/* Left: Asset Info */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                        <div className="p-2 rounded-lg bg-slate-800/50">
                            {assetTypeIcons[asset.type] || <Globe className="h-5 w-5" />}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <h3 className="text-white font-medium truncate">{asset.name}</h3>
                                {!isActive && (
                                    <Badge variant="outline" className="border-slate-600 text-slate-400 text-xs">
                                        {asset.status}
                                    </Badge>
                                )}
                            </div>
                            <p className="text-xs text-slate-500">{assetTypeLabels[asset.type]}</p>
                            {asset.external_id && (
                                <p className="text-xs text-slate-600 truncate mt-1">{asset.external_id}</p>
                            )}
                        </div>
                    </div>

                    {/* Right: Risk Score */}
                    <div className="text-right">
                        {asset.last_risk_score !== null ? (
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${getRiskColor(asset.last_risk_score)}`} />
                                <span className="text-lg font-bold text-white">{asset.last_risk_score}</span>
                            </div>
                        ) : (
                            <span className="text-sm text-slate-500">No scan</span>
                        )}
                    </div>
                </div>

                {/* Scan Info */}
                <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-400">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Last: {formatDate(asset.last_scan_at)}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                        <Clock className="h-3.5 w-3.5" />
                        <span>Next: {formatRelativeDate(asset.next_scan_at)}</span>
                    </div>
                </div>

                {/* Actions */}
                <div className="mt-4 flex items-center gap-2">
                    {/* Frequency Selector */}
                    <Select
                        value={asset.scan_frequency}
                        onValueChange={(v) => onUpdateFrequency(asset.id, v as ScanFrequency)}
                        disabled={isUpdating || !isActive}
                    >
                        <SelectTrigger className="h-8 w-[120px] bg-slate-800 border-slate-700 text-xs text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="daily" className="text-white text-xs hover:bg-slate-700">Daily</SelectItem>
                            <SelectItem value="weekly" className="text-white text-xs hover:bg-slate-700">Weekly</SelectItem>
                            <SelectItem value="monthly" className="text-white text-xs hover:bg-slate-700">Monthly</SelectItem>
                            <SelectItem value="manual" className="text-white text-xs hover:bg-slate-700">Manual</SelectItem>
                        </SelectContent>
                    </Select>

                    {/* Scan Now Button */}
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={handleScan}
                        disabled={isScanning || !isActive || asset.type !== 'domain'}
                        className="h-8 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                    >
                        {isScanning ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <>
                                <Play className="h-3.5 w-3.5 mr-1" />
                                Scan
                            </>
                        )}
                    </Button>

                    {/* Delete Button */}
                    <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleDelete}
                        disabled={isDeleting}
                        className="h-8 text-slate-500 hover:text-red-400 hover:bg-red-500/10 ml-auto"
                    >
                        {isDeleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                        )}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
