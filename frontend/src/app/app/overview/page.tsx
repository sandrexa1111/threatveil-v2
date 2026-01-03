'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyStatePrompts, NextActionCard } from '@/components/EmptyStatePrompts';
import { getOrgOverview } from '@/lib/api/scans';
import { OrgOverview, AssetWithRisk, DecisionSummary } from '@/lib/types';
import {
    TrendingUp,
    TrendingDown,
    Minus,
    Shield,
    Bot,
    Server,
    AlertTriangle,
    ArrowRight,
    CheckCircle,
    Activity
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import {
    AreaChart,
    Area,
    ResponsiveContainer,
    Tooltip as RechartsTooltip,
    XAxis
} from 'recharts';

// Use default org for now (would come from auth context in production)
const DEFAULT_ORG_ID = 'demo-org';

function TrendIndicator({ value, size = 'md' }: { value: number; size?: 'sm' | 'md' }) {
    const isPositive = value > 0;
    const isNeutral = value === 0;

    return (
        <span className={cn(
            'inline-flex items-center gap-0.5 font-medium',
            size === 'sm' ? 'text-xs' : 'text-sm',
            isNeutral ? 'text-slate-400' : (isPositive ? 'text-red-400' : 'text-emerald-400')
        )}>
            {isNeutral ? (
                <Minus className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
            ) : isPositive ? (
                <TrendingUp className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
            ) : (
                <TrendingDown className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
            )}
            {Math.abs(value)}%
        </span>
    );
}

function RiskScoreGauge({ score, trend30d }: { score: number; trend30d: number }) {
    const getRiskLevel = (s: number) => {
        if (s >= 70) return { label: 'Critical', color: 'from-red-500 to-rose-600' };
        if (s >= 50) return { label: 'High', color: 'from-orange-500 to-amber-600' };
        if (s >= 30) return { label: 'Medium', color: 'from-yellow-500 to-amber-500' };
        return { label: 'Low', color: 'from-emerald-500 to-green-600' };
    };

    const risk = getRiskLevel(score);

    return (
        <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    Organization Risk Score
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-end justify-between">
                    <div>
                        <div className={cn(
                            'text-5xl font-bold bg-gradient-to-r bg-clip-text text-transparent',
                            risk.color
                        )}>
                            {score}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className={cn(
                                'text-xs border-0',
                                score >= 70 ? 'bg-red-500/20 text-red-400' :
                                    score >= 50 ? 'bg-orange-500/20 text-orange-400' :
                                        score >= 30 ? 'bg-yellow-500/20 text-yellow-400' :
                                            'bg-emerald-500/20 text-emerald-400'
                            )}>
                                {risk.label} Risk
                            </Badge>
                            <TrendIndicator value={trend30d} />
                            <span className="text-xs text-slate-500">vs 30d ago</span>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function AIPostureCard({ score, trend, status }: { score: number; trend: number; status: string }) {
    const statusConfig = {
        clean: { color: 'text-emerald-400', bg: 'bg-emerald-500/20', label: 'AI-Clean' },
        warning: { color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Moderate' },
        critical: { color: 'text-red-400', bg: 'bg-red-500/20', label: 'Critical' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.clean;

    return (
        <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    AI Security Posture
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-3xl font-bold text-white">{score}</div>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge className={cn('text-xs border-0', config.bg, config.color)}>
                                {config.label}
                            </Badge>
                            <TrendIndicator value={trend} size="sm" />
                        </div>
                    </div>
                    <Link href="/app/ai-security">
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                            View Details
                            <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                    </Link>
                </div>
            </CardContent>
        </Card>
    );
}

function TopDecisionsList({ decisions }: { decisions: DecisionSummary[] }) {
    if (decisions.length === 0) {
        return (
            <Card className="border-slate-800 bg-slate-900/50">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        Priority Actions
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-8 text-center">
                        <div>
                            <CheckCircle className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
                            <p className="text-slate-400">No pending actions</p>
                            <p className="text-xs text-slate-500">Great job staying on top of security!</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Priority Actions This Week
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {decisions.slice(0, 5).map((decision, i) => (
                    <div
                        key={decision.id}
                        className="flex items-start justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                    >
                        <div className="flex items-start gap-3">
                            <div className={cn(
                                'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold',
                                i === 0 ? 'bg-red-500/20 text-red-400' :
                                    i === 1 ? 'bg-orange-500/20 text-orange-400' :
                                        'bg-slate-700 text-slate-400'
                            )}>
                                {i + 1}
                            </div>
                            <div>
                                <p className="font-medium text-white text-sm">{decision.title}</p>
                                <p className="text-xs text-slate-400">
                                    {decision.effort_estimate} · -{decision.estimated_risk_reduction}% risk
                                </p>
                            </div>
                        </div>
                        <Badge
                            variant="outline"
                            className={cn(
                                'text-xs border-0',
                                decision.status === 'pending' ? 'bg-slate-700 text-slate-300' :
                                    decision.status === 'accepted' ? 'bg-amber-500/20 text-amber-400' :
                                        decision.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                                            'bg-emerald-500/20 text-emerald-400'
                            )}
                        >
                            {decision.status}
                        </Badge>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}

function TopRiskyAssets({ assets }: { assets: AssetWithRisk[] }) {
    if (assets.length === 0) {
        return null;
    }

    return (
        <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    Highest Risk Assets
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {assets.slice(0, 3).map((asset) => (
                    <Link
                        key={asset.id}
                        href={`/app/assets/${asset.id}`}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <Server className="h-5 w-5 text-slate-500" />
                            <div>
                                <p className="font-medium text-white text-sm">{asset.name}</p>
                                <p className="text-xs text-slate-400">{asset.type}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className={cn(
                                'font-bold',
                                (asset.current_risk_score || 0) >= 70 ? 'text-red-400' :
                                    (asset.current_risk_score || 0) >= 50 ? 'text-orange-400' :
                                        (asset.current_risk_score || 0) >= 30 ? 'text-yellow-400' :
                                            'text-emerald-400'
                            )}>
                                {asset.current_risk_score || 0}
                            </div>
                            {asset.risk_trend !== null && (
                                <TrendIndicator value={asset.risk_trend} size="sm" />
                            )}
                        </div>
                    </Link>
                ))}
                <Link href="/app/assets">
                    <Button variant="ghost" size="sm" className="w-full text-slate-400 hover:text-white">
                        View All Assets
                        <ArrowRight className="h-4 w-4 ml-1" />
                    </Button>
                </Link>
            </CardContent>
        </Card>
    );
}

function UsageSummaryCard({ scansUsed, scansLimit, plan }: { scansUsed: number; scansLimit: number; plan: string }) {
    const usagePercent = (scansUsed / scansLimit) * 100;

    return (
        <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Usage This Month
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl font-bold text-white">{scansUsed}</span>
                    <span className="text-sm text-slate-400">/ {scansLimit} scans</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                        className={cn(
                            'h-full rounded-full transition-all',
                            usagePercent >= 90 ? 'bg-red-500' :
                                usagePercent >= 70 ? 'bg-amber-500' :
                                    'bg-cyan-500'
                        )}
                        style={{ width: `${Math.min(usagePercent, 100)}%` }}
                    />
                </div>
                <div className="flex items-center justify-between mt-2">
                    <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
                        {plan.charAt(0).toUpperCase() + plan.slice(1)} Plan
                    </Badge>
                    {usagePercent >= 80 && (
                        <span className="text-xs text-amber-400">Consider upgrading</span>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

export default function OverviewPage() {
    const [overview, setOverview] = useState<OrgOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadOverview() {
            try {
                setLoading(true);
                const data = await getOrgOverview(DEFAULT_ORG_ID);
                setOverview(data);
            } catch (err) {
                console.error('Failed to load overview:', err);
                setError('Failed to load organization overview');
            } finally {
                setLoading(false);
            }
        }

        loadOverview();
    }, []);

    if (loading) {
        return (
            <div className="space-y-6 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <Skeleton className="h-8 w-64 mb-2" />
                        <Skeleton className="h-4 w-96" />
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-40" />
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="text-center py-12">
                    <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-white mb-2">Unable to Load Overview</h2>
                    <p className="text-slate-400">{error}</p>
                </div>
            </div>
        );
    }

    // Show empty state if no assets
    if (!overview || overview.total_assets === 0) {
        return (
            <div className="p-6">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white">Security Overview</h1>
                    <p className="text-slate-400">Your organization&apos;s security posture at a glance</p>
                </div>
                <EmptyStatePrompts type="overview" />
            </div>
        );
    }

    return (
        <motion.div
            className="p-6 space-y-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">
                        {overview.org_name || 'Security Overview'}
                    </h1>
                    <p className="text-slate-400">
                        Monitoring {overview.total_assets} asset{overview.total_assets !== 1 ? 's' : ''} across your organization
                    </p>
                </div>
                <Link href="/app/scans">
                    <Button className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400">
                        <Activity className="h-4 w-4 mr-2" />
                        New Scan
                    </Button>
                </Link>
            </div>

            {/* Next Action Card if applicable */}
            {overview.unresolved_decisions_count > 0 && (
                <NextActionCard
                    title="Next Recommended Action"
                    description={`You have ${overview.unresolved_decisions_count} pending security action${overview.unresolved_decisions_count !== 1 ? 's' : ''} to review.`}
                    actionLabel="Review Actions"
                    actionHref="/app/horizon"
                />
            )}

            {/* Main Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <RiskScoreGauge
                    score={overview.total_risk_score}
                    trend30d={overview.risk_trend_30d}
                />
                <AIPostureCard
                    score={overview.ai_posture.score}
                    trend={overview.ai_posture.trend}
                    status={overview.ai_posture.status}
                />
                <UsageSummaryCard
                    scansUsed={overview.total_scans_this_month}
                    scansLimit={overview.scans_limit}
                    plan={overview.plan}
                />
            </div>

            {/* Decisions and Assets */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TopDecisionsList decisions={overview.decisions_this_week} />
                <TopRiskyAssets assets={overview.top_risky_assets} />
            </div>
        </motion.div>
    );
}
