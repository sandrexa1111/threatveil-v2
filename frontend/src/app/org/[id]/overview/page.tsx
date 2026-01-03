'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    ArrowLeft,
    Loader2,
    TrendingUp,
    TrendingDown,
    Minus,
    ShieldAlert,
    Brain,
    ListChecks,
    Globe,
    Github,
    Cloud,
    Package,
    Activity,
    Zap
} from 'lucide-react';
import { getOrgOverview } from '@/lib/api/assets';
import type { OrgOverview, DecisionSummary, AssetWithRisk } from '@/lib/types';

const assetTypeIcons: Record<string, React.ReactNode> = {
    domain: <Globe className="h-4 w-4" />,
    github_org: <Github className="h-4 w-4" />,
    cloud_account: <Cloud className="h-4 w-4" />,
    saas_vendor: <Package className="h-4 w-4" />,
};

function TrendIndicator({ value, size = 'md' }: { value: number; size?: 'sm' | 'md' }) {
    const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
    const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

    if (value > 0) {
        return (
            <span className={`flex items-center gap-0.5 text-red-400 ${textSize}`}>
                <TrendingUp className={iconSize} />
                +{value}
            </span>
        );
    } else if (value < 0) {
        return (
            <span className={`flex items-center gap-0.5 text-emerald-400 ${textSize}`}>
                <TrendingDown className={iconSize} />
                {value}
            </span>
        );
    }
    return (
        <span className={`flex items-center gap-0.5 text-slate-500 ${textSize}`}>
            <Minus className={iconSize} />
            0
        </span>
    );
}

function RiskScoreGauge({ score, label }: { score: number; label: string }) {
    const color = score >= 70 ? 'text-red-500' : score >= 40 ? 'text-amber-500' : 'text-emerald-500';
    const bgColor = score >= 70 ? 'bg-red-500' : score >= 40 ? 'bg-amber-500' : 'bg-emerald-500';

    return (
        <div className="flex flex-col items-center">
            <div className="relative w-24 h-24">
                <svg className="w-24 h-24 -rotate-90" viewBox="0 0 36 36">
                    <circle
                        cx="18" cy="18" r="15.91549431"
                        fill="transparent"
                        stroke="currentColor"
                        strokeWidth="3"
                        className="text-slate-800"
                    />
                    <circle
                        cx="18" cy="18" r="15.91549431"
                        fill="transparent"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeDasharray={`${score} ${100 - score}`}
                        strokeLinecap="round"
                        className={color}
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-2xl font-bold ${color}`}>{score}</span>
                </div>
            </div>
            <span className="text-xs text-slate-400 mt-2">{label}</span>
        </div>
    );
}

function AIPostureCard({ posture }: { posture: OrgOverview['ai_posture'] }) {
    const statusColors = {
        clean: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
        warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
        critical: 'bg-red-500/10 text-red-400 border-red-500/30',
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-400" />
                    AI Exposure Posture
                </CardTitle>
                <Badge className={`${statusColors[posture.status]} border`}>
                    {posture.status.toUpperCase()}
                </Badge>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-3xl font-bold text-white">{posture.score}</p>
                        <p className="text-xs text-slate-500 mt-1">AI Risk Score</p>
                    </div>
                    <TrendIndicator value={posture.trend} />
                </div>
            </CardContent>
        </Card>
    );
}

function TopRiskyAssetsCard({ assets }: { assets: AssetWithRisk[] }) {
    if (assets.length === 0) {
        return (
            <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-amber-400" />
                        Top Risky Assets
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-slate-500 text-center py-8">No risky assets detected</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                    Top Risky Assets
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {assets.map((asset, i) => (
                    <div
                        key={asset.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800"
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500 w-4">{i + 1}.</span>
                            <div className="p-1.5 rounded bg-slate-800">
                                {assetTypeIcons[asset.type] || <Globe className="h-4 w-4" />}
                            </div>
                            <div>
                                <p className="text-sm font-medium text-white">{asset.name}</p>
                                <p className="text-xs text-slate-500">{asset.signal_count} signals</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-lg font-bold text-white">{asset.current_risk_score ?? asset.last_risk_score ?? 0}</span>
                            {asset.risk_trend !== null && <TrendIndicator value={asset.risk_trend} size="sm" />}
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}

function DecisionsThisWeekCard({ decisions, count }: { decisions: DecisionSummary[]; count: number }) {
    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                    <ListChecks className="h-4 w-4 text-cyan-400" />
                    This Week&apos;s Decisions
                </CardTitle>
                {count > 0 && (
                    <Badge variant="outline" className="border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
                        {count} pending
                    </Badge>
                )}
            </CardHeader>
            <CardContent>
                {decisions.length === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-8">No decisions this week</p>
                ) : (
                    <div className="space-y-3">
                        {decisions.slice(0, 5).map((decision) => (
                            <div
                                key={decision.id}
                                className="flex items-start justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800"
                            >
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white truncate">{decision.title}</p>
                                    {decision.business_impact && (
                                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">{decision.business_impact}</p>
                                    )}
                                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                                        <span>⏱ {decision.effort_estimate}</span>
                                        <span>📉 -{decision.estimated_risk_reduction} pts</span>
                                    </div>
                                </div>
                                <Badge
                                    variant="outline"
                                    className={
                                        decision.confidence_score >= 0.8
                                            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                                            : decision.confidence_score >= 0.5
                                                ? 'border-amber-500/30 bg-amber-500/10 text-amber-400'
                                                : 'border-slate-500/30 bg-slate-500/10 text-slate-400'
                                    }
                                >
                                    {Math.round(decision.confidence_score * 100)}%
                                </Badge>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function UsageLimitsCard({ overview }: { overview: OrgOverview }) {
    const usagePercent = (overview.total_scans_this_month / overview.scans_limit) * 100;
    const isNearLimit = usagePercent >= 80;

    const planColors = {
        free: 'border-slate-500/30 bg-slate-500/10 text-slate-400',
        pro: 'border-purple-500/30 bg-purple-500/10 text-purple-400',
        enterprise: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-400" />
                    Usage & Plan
                </CardTitle>
                <Badge className={`${planColors[overview.plan]} border`}>
                    {overview.plan.toUpperCase()}
                </Badge>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Scans this month</span>
                        <span className={isNearLimit ? 'text-amber-400' : 'text-white'}>
                            {overview.total_scans_this_month} / {overview.scans_limit}
                        </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all ${isNearLimit ? 'bg-amber-500' : 'bg-purple-500'}`}
                            style={{ width: `${Math.min(usagePercent, 100)}%` }}
                        />
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Total assets</span>
                        <span className="text-white">{overview.total_assets}</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function AssetsByTypeCard({ assetsByType }: { assetsByType: Record<string, number> }) {
    const total = Object.values(assetsByType).reduce((a, b) => a + b, 0);

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader>
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Activity className="h-4 w-4 text-cyan-400" />
                    Assets by Type
                </CardTitle>
            </CardHeader>
            <CardContent>
                {total === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-4">No assets yet</p>
                ) : (
                    <div className="space-y-3">
                        {Object.entries(assetsByType).map(([type, count]) => (
                            <div key={type} className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-slate-400">
                                    {assetTypeIcons[type] || <Globe className="h-4 w-4" />}
                                    <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                                </div>
                                <span className="text-sm font-medium text-white">{count}</span>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default function OrgOverviewPage() {
    const params = useParams();
    const orgId = params.id as string;

    const [overview, setOverview] = useState<OrgOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!orgId) return;

        getOrgOverview(orgId)
            .then((data) => {
                setOverview(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error(err);
                setError('Failed to load organization data');
                setLoading(false);
            });
    }, [orgId]);

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            </div>
        );
    }

    if (error || !overview) {
        return (
            <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
                <p className="text-lg text-gray-400">{error || 'Organization not found'}</p>
                <Link href="/app">
                    <Button variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Dashboard
                    </Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0B0F19] to-[#111827]">
            <div className="mx-auto max-w-7xl space-y-6 px-4 sm:px-6 lg:px-8 py-8">
                {/* Back button */}
                <Link href="/app">
                    <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-gray-800/50 -ml-2">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Dashboard
                    </Button>
                </Link>

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">
                            {overview.org_name || 'Organization'} Overview
                        </h1>
                        <p className="text-slate-400 mt-1">The control room for your company&apos;s security</p>
                    </div>
                    <Link href="/app/assets">
                        <Button className="bg-purple-600 hover:bg-purple-700 text-white">
                            Manage Assets
                        </Button>
                    </Link>
                </div>

                {/* Hero Risk Score Section */}
                <Card className="border-slate-800 bg-gradient-to-r from-slate-900/80 to-purple-900/20 backdrop-blur-sm">
                    <CardContent className="py-8">
                        <div className="flex items-center justify-around">
                            <RiskScoreGauge score={overview.total_risk_score} label="Total Risk Score" />
                            <div className="flex flex-col items-center gap-4">
                                <div className="text-center">
                                    <p className="text-sm text-slate-400 mb-1">30-Day Trend</p>
                                    <TrendIndicator value={overview.risk_trend_30d} size="md" />
                                </div>
                            </div>
                            <div className="flex flex-col items-center gap-4">
                                <div className="text-center">
                                    <p className="text-sm text-slate-400 mb-1">90-Day Trend</p>
                                    <TrendIndicator value={overview.risk_trend_90d} size="md" />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Main Grid */}
                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Left Column - AI Posture & Usage */}
                    <div className="space-y-6">
                        <AIPostureCard posture={overview.ai_posture} />
                        <UsageLimitsCard overview={overview} />
                        <AssetsByTypeCard assetsByType={overview.assets_by_type} />
                    </div>

                    {/* Center Column - Top Risky Assets */}
                    <TopRiskyAssetsCard assets={overview.top_risky_assets} />

                    {/* Right Column - Decisions */}
                    <DecisionsThisWeekCard
                        decisions={overview.decisions_this_week}
                        count={overview.unresolved_decisions_count}
                    />
                </div>

                {/* Last Updated */}
                {overview.last_updated && (
                    <p className="text-xs text-slate-600 text-center">
                        Last updated: {new Date(overview.last_updated).toLocaleString()}
                    </p>
                )}
            </div>
        </div>
    );
}
