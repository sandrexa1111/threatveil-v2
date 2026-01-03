'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Newspaper, CheckCircle2, TrendingDown, Sparkles, RefreshCw } from 'lucide-react';
import type { DecisionSummary } from '@/lib/types';

interface WeeklyBriefCardProps {
    headline: string;
    topChanges: string[];
    top3Actions: DecisionSummary[];
    aiExposureSummary: string;
    confidenceLevel: 'low' | 'medium' | 'high';
    explanation?: string | null;
    generatedAt?: string;
    isLoading?: boolean;
    onRefresh?: () => void;
}

/**
 * WeeklyBriefCard - Executive summary card for Horizon dashboard
 * 
 * Shows:
 * - Headline (bold, prominent)
 * - Top changes (completed items)
 * - Top 3 priority actions
 * - AI-generated explanation (if available)
 * - Confidence indicator
 */
export function WeeklyBriefCard({
    headline,
    topChanges,
    top3Actions,
    aiExposureSummary,
    confidenceLevel,
    explanation,
    generatedAt,
    isLoading = false,
    onRefresh,
}: WeeklyBriefCardProps) {
    const getConfidenceBadgeStyle = () => {
        switch (confidenceLevel) {
            case 'high':
                return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
            case 'medium':
                return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
            case 'low':
                return 'bg-slate-500/10 border-slate-500/30 text-slate-400';
        }
    };

    const formatDate = (dateStr: string | undefined) => {
        if (!dateStr) return '';
        try {
            return new Date(dateStr).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
            });
        } catch {
            return '';
        }
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                        <Newspaper className="h-4 w-4 text-purple-400" />
                        Weekly Security Brief
                    </CardTitle>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getConfidenceBadgeStyle()}>
                            {confidenceLevel} confidence
                        </Badge>
                        {onRefresh && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={onRefresh}
                                disabled={isLoading}
                                className="text-slate-400 hover:text-white"
                            >
                                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                            </Button>
                        )}
                    </div>
                </div>
                {generatedAt && (
                    <p className="text-xs text-slate-500 mt-1">
                        Generated {formatDate(generatedAt)}
                    </p>
                )}
            </CardHeader>

            <CardContent className="space-y-5">
                {/* Headline */}
                <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white leading-tight">
                        {headline}
                    </h3>
                </div>

                {/* Top Changes (completed items) */}
                {topChanges.length > 0 && (
                    <div>
                        <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                            Completed This Week
                        </h4>
                        <div className="space-y-2">
                            {topChanges.slice(0, 5).map((change, i) => (
                                <div key={i} className="flex items-start gap-2 text-sm">
                                    <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                                    <span className="text-slate-300">{change}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Top 3 Priority Actions */}
                {top3Actions.length > 0 && (
                    <div>
                        <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                            Priority Actions
                        </h4>
                        <div className="space-y-2">
                            {top3Actions.map((action, i) => (
                                <div
                                    key={action.id}
                                    className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 border border-slate-800"
                                >
                                    <div className="flex-shrink-0 h-6 w-6 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                                        <span className="text-xs font-bold text-purple-400">{i + 1}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate">{action.title}</p>
                                        <div className="flex items-center gap-3 text-xs text-slate-500">
                                            <span className="flex items-center gap-1">
                                                <TrendingDown className="h-3 w-3 text-emerald-400" />
                                                -{action.estimated_risk_reduction}% risk
                                            </span>
                                            <span>{action.effort_estimate}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* AI Explanation (if available) */}
                {explanation && (
                    <div className="p-3 rounded-lg bg-purple-500/5 border border-purple-500/20">
                        <div className="flex items-center gap-2 text-xs text-purple-300 mb-2">
                            <Sparkles className="h-3.5 w-3.5" />
                            AI Summary
                        </div>
                        <p className="text-sm text-slate-300 leading-relaxed">
                            {explanation}
                        </p>
                    </div>
                )}

                {/* Empty state */}
                {topChanges.length === 0 && top3Actions.length === 0 && (
                    <div className="text-center py-6">
                        <p className="text-sm text-slate-500">
                            No activity this week. Run a scan to generate insights.
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
