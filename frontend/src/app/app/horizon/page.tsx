'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
    Loader2, Calendar, RefreshCw, Share2, Printer, Shield,
    TrendingDown, TrendingUp, AlertTriangle, Brain, Copy, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';
import { getHorizonData, getWeeklyBrief } from '@/lib/api/scans';
import type { HorizonData, WeeklyBrief } from '@/lib/types';
import { StatCard, SectionHeader, SkeletonStats, SkeletonCard } from '@/components/ui-kit';
import {
    RiskTrendCard,
    AIExposureSummary,
    WeeklyBriefCard,
    TopDecisionsList,
    ImpactThisWeek,
    AssetsPanel,
    RiskReductionTimeline,
} from '@/components/horizon';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// Default org ID for demo
const DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001';

export default function HorizonPage() {
    const [horizonData, setHorizonData] = useState<HorizonData | null>(null);
    const [weeklyBrief, setWeeklyBrief] = useState<WeeklyBrief | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showShareModal, setShowShareModal] = useState(false);

    const fetchData = useCallback(async (showRefreshIndicator = false) => {
        if (showRefreshIndicator) {
            setIsRefreshing(true);
        } else {
            setIsLoading(true);
        }
        setError(null);

        try {
            const [horizon, brief] = await Promise.all([
                getHorizonData(DEFAULT_ORG_ID),
                getWeeklyBrief(DEFAULT_ORG_ID),
            ]);

            setHorizonData(horizon);
            setWeeklyBrief(brief);
        } catch (err) {
            console.error('Failed to fetch Horizon data:', err);
            setError('Failed to load Horizon data. Please try again.');
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleRefresh = () => {
        fetchData(true);
    };

    // Loading state
    if (isLoading) {
        return (
            <div className="space-y-8 animate-fade-in">
                <div className="flex items-center justify-between">
                    <div className="space-y-2">
                        <div className="h-8 w-40 rounded bg-slate-800/60 animate-pulse" />
                        <div className="h-4 w-64 rounded bg-slate-800/40 animate-pulse" />
                    </div>
                    <div className="h-9 w-24 rounded bg-slate-800/60 animate-pulse" />
                </div>
                <SkeletonStats count={4} />
                <SkeletonCard />
                <div className="grid gap-6 lg:grid-cols-5">
                    <div className="lg:col-span-3">
                        <SkeletonCard />
                    </div>
                    <div className="lg:col-span-2">
                        <SkeletonCard />
                    </div>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center justify-center min-h-[400px]"
            >
                <div className="text-center">
                    <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20 w-fit mx-auto mb-4">
                        <AlertTriangle className="h-8 w-8 text-red-400" />
                    </div>
                    <p className="text-red-400 mb-4">{error}</p>
                    <Button onClick={() => fetchData()} variant="outline" className="border-slate-700">
                        Try Again
                    </Button>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
        >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-cyan-500/10">
                            <Calendar className="h-6 w-6 text-cyan-400" />
                        </div>
                        Horizon
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">
                        Your weekly security posture at a glance
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        onClick={() => setShowShareModal(true)}
                        variant="outline"
                        size="sm"
                        className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                    >
                        <Share2 className="h-4 w-4 mr-2" />
                        Share Brief
                    </Button>
                    <Button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium"
                    >
                        <RefreshCw className={cn('h-4 w-4 mr-2', isRefreshing && 'animate-spin')} />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Top Row: Key Metrics */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                    label="Current Risk"
                    value={horizonData?.current_risk_score ?? 0}
                    icon={Shield}
                    variant={
                        (horizonData?.current_risk_score ?? 0) >= 70 ? 'danger' :
                            (horizonData?.current_risk_score ?? 0) >= 30 ? 'warning' : 'success'
                    }
                    trend={horizonData?.risk_trend ? {
                        value: horizonData.risk_trend,
                        direction: horizonData.risk_trend > 0 ? 'up' : horizonData.risk_trend < 0 ? 'down' : 'neutral',
                        label: 'pts',
                    } : undefined}
                />

                <StatCard
                    label="Risk Trend"
                    value={`${horizonData?.risk_trend && horizonData.risk_trend > 0 ? '+' : ''}${horizonData?.risk_trend ?? 0}`}
                    icon={horizonData?.risk_trend && horizonData.risk_trend > 0 ? TrendingUp : TrendingDown}
                    variant={
                        (horizonData?.risk_trend ?? 0) > 0 ? 'danger' :
                            (horizonData?.risk_trend ?? 0) < 0 ? 'success' : 'default'
                    }
                />

                <StatCard
                    label="AI Posture"
                    value={horizonData?.ai_posture.score ?? 0}
                    icon={Brain}
                    variant={
                        horizonData?.ai_posture.status === 'critical' ? 'danger' :
                            horizonData?.ai_posture.status === 'warning' ? 'warning' : 'accent'
                    }
                    trend={horizonData?.ai_posture.trend ? {
                        value: horizonData.ai_posture.trend,
                        direction: horizonData.ai_posture.trend > 0 ? 'up' : horizonData.ai_posture.trend < 0 ? 'down' : 'neutral',
                    } : undefined}
                />

                <StatCard
                    label="Unresolved Critical"
                    value={horizonData?.unresolved_critical_signals ?? 0}
                    icon={AlertTriangle}
                    variant={(horizonData?.unresolved_critical_signals ?? 0) > 0 ? 'danger' : 'success'}
                />
            </div>

            {/* Phase 2: Risk Reduction Timeline */}
            <RiskReductionTimeline orgId={DEFAULT_ORG_ID} />

            {/* Main Content: Weekly Brief + Top Decisions */}
            <div className="grid gap-6 lg:grid-cols-5 items-start">
                {/* Weekly Brief + Impact - takes more space */}
                <div className="lg:col-span-3 space-y-6">
                    <WeeklyBriefCard
                        headline={weeklyBrief?.headline ?? 'No data available'}
                        topChanges={weeklyBrief?.top_changes ?? []}
                        top3Actions={weeklyBrief?.top_3_actions ?? []}
                        aiExposureSummary={weeklyBrief?.ai_exposure_summary ?? ''}
                        confidenceLevel={weeklyBrief?.confidence_level ?? 'low'}
                        explanation={weeklyBrief?.explanation}
                        generatedAt={weeklyBrief?.generated_at}
                        isLoading={isRefreshing}
                        onRefresh={handleRefresh}
                    />

                    {weeklyBrief?.decision_impacts && weeklyBrief.decision_impacts.length > 0 && (
                        <ImpactThisWeek impacts={weeklyBrief.decision_impacts} />
                    )}
                </div>

                {/* Top Decisions + Assets - sidebar */}
                <div className="lg:col-span-2 space-y-6">
                    <TopDecisionsList
                        decisions={horizonData?.top_decisions ?? []}
                    />

                    <AssetsPanel
                        assets={horizonData?.assets_summary ?? []}
                    />
                </div>
            </div>

            {/* Footer note */}
            <div className="text-center py-4">
                <p className="text-xs text-slate-600">
                    Horizon aggregates data from your latest scans to provide a weekly security overview.
                    Run regular scans to improve confidence levels.
                </p>
            </div>

            {/* Share Brief Modal */}
            <ShareBriefModal
                open={showShareModal}
                onOpenChange={setShowShareModal}
                weeklyBrief={weeklyBrief}
                horizonData={horizonData}
            />
        </motion.div>
    );
}

// Share Brief Modal Component
function ShareBriefModal({
    open,
    onOpenChange,
    weeklyBrief,
    horizonData,
}: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    weeklyBrief: WeeklyBrief | null;
    horizonData: HorizonData | null;
}) {
    const [copied, setCopied] = useState(false);
    const briefRef = useRef<HTMLDivElement>(null);

    const generateBriefText = () => {
        if (!weeklyBrief || !horizonData) return '';

        const lines = [
            `🔒 THREATVEIL WEEKLY SECURITY BRIEF`,
            `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
            ``,
            `📊 CURRENT STATUS`,
            `Risk Score: ${horizonData.current_risk_score}/100`,
            `AI Posture: ${horizonData.ai_posture.score}/100`,
            `Unresolved Critical: ${horizonData.unresolved_critical_signals}`,
            ``,
            `📰 HEADLINE`,
            weeklyBrief.headline,
            ``,
            `🔄 KEY CHANGES`,
            ...weeklyBrief.top_changes.map((c, i) => `${i + 1}. ${c}`),
            ``,
            `⚡ TOP ACTIONS`,
            ...weeklyBrief.top_3_actions.map((a, i) => `${i + 1}. ${a.title} (${a.effort_estimate})`),
            ``,
            `🤖 AI EXPOSURE`,
            weeklyBrief.ai_exposure_summary,
            ``,
            `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
            `Generated by ThreatVeil`,
        ];

        return lines.join('\n');
    };

    const handleCopy = async () => {
        const text = generateBriefText();
        await navigator.clipboard.writeText(text);
        setCopied(true);
        toast.success('Brief copied to clipboard');
        setTimeout(() => setCopied(false), 2000);
    };

    const handlePrint = () => {
        window.print();
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-2xl bg-slate-950 border-slate-800 max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="text-white flex items-center gap-2">
                        <Share2 className="h-5 w-5 text-cyan-400" />
                        Share Weekly Brief
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Copy or print your weekly security brief to share with your team.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                    {/* Actions */}
                    <div className="flex gap-2">
                        <Button
                            onClick={handleCopy}
                            className="flex-1 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium"
                        >
                            {copied ? (
                                <>
                                    <Check className="h-4 w-4 mr-2" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="h-4 w-4 mr-2" />
                                    Copy to Clipboard
                                </>
                            )}
                        </Button>
                        <Button
                            onClick={handlePrint}
                            variant="outline"
                            className="flex-1 border-slate-700 text-slate-300 hover:bg-slate-800"
                        >
                            <Printer className="h-4 w-4 mr-2" />
                            Print
                        </Button>
                    </div>

                    {/* Preview */}
                    <div
                        ref={briefRef}
                        className="bg-slate-900 rounded-xl border border-slate-800 p-6 font-mono text-sm text-slate-300 whitespace-pre-wrap print:bg-white print:text-black"
                    >
                        {generateBriefText()}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
