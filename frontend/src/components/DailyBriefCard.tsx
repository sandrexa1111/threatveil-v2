'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Newspaper, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Minus, Brain, ArrowRight } from 'lucide-react';
import { AIExposureBadgeFromLevel } from './AIExposureBadge';
import Link from 'next/link';

interface DailyBriefCardProps {
    topSignals?: Array<{
        id: string;
        title: string;
        severity: string;
    }>;
    topActions?: string[];
    riskDelta?: number;
    aiExposure?: 'low' | 'moderate' | 'high';
    lastScanId?: string | null;
    isLoading?: boolean;
}

/**
 * DailyBriefCard - Daily security brief placeholder (Phase 2 feature)
 * 
 * Shows:
 * - Top 3 priority signals
 * - Top 3 recommended actions
 * - Risk trend indicator
 * - AI exposure level
 */
export function DailyBriefCard({
    topSignals = [],
    topActions = [],
    riskDelta = 0,
    aiExposure = 'low',
    lastScanId = null,
    isLoading = false,
}: DailyBriefCardProps) {
    const getTrendIcon = () => {
        if (riskDelta > 0) return <TrendingUp className="h-4 w-4 text-red-400" />;
        if (riskDelta < 0) return <TrendingDown className="h-4 w-4 text-emerald-400" />;
        return <Minus className="h-4 w-4 text-slate-400" />;
    };

    const getTrendText = () => {
        if (riskDelta > 0) return `+${riskDelta.toFixed(1)}% risk`;
        if (riskDelta < 0) return `${riskDelta.toFixed(1)}% risk`;
        return 'No change';
    };

    return (
        <Card className="border-slate-700 bg-slate-900 backdrop-blur-sm relative overflow-hidden">
            {/* Beta badge */}
            <div className="absolute top-3 right-3">
                <Badge
                    variant="outline"
                    className="bg-purple-500/20 border-purple-400/50 text-purple-200 text-[10px] uppercase tracking-wider"
                >
                    Beta
                </Badge>
            </div>

            <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                    <Newspaper className="h-4 w-4 text-purple-400" />
                    Daily Security Brief
                </CardTitle>
                <p className="text-xs text-slate-300 mt-1">
                    AI-powered insights delivered every day
                </p>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* Top Signals */}
                <div>
                    <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                        Priority Signals
                    </h4>
                    <div className="space-y-2">
                        {topSignals.length > 0 ? (
                            topSignals.slice(0, 3).map((signal, i) => (
                                <div
                                    key={signal.id || i}
                                    className="flex items-center gap-2 text-sm"
                                >
                                    <AlertTriangle className={`h-3 w-3 ${signal.severity === 'critical' ? 'text-red-400' :
                                        signal.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'
                                        }`} />
                                    <span className="text-slate-300 truncate flex-1">{signal.title}</span>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-slate-500 italic">No critical signals</p>
                        )}
                    </div>
                </div>

                {/* Top Actions */}
                <div>
                    <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                        Recommended Actions
                    </h4>
                    <div className="space-y-2">
                        {topActions.slice(0, 3).map((action, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm">
                                <CheckCircle2 className="h-3 w-3 text-emerald-400 mt-0.5 shrink-0" />
                                <span className="text-slate-300">{action}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Metrics Row */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <div className="flex items-center gap-2">
                        {getTrendIcon()}
                        <span className="text-xs text-slate-400">{getTrendText()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Brain className="h-3 w-3 text-slate-500" />
                        <AIExposureBadgeFromLevel level={aiExposure} size="sm" />
                    </div>
                </div>

                {/* View Details Link */}
                {lastScanId && (
                    <Link href={`/app/scans/${lastScanId}`}>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="w-full text-purple-300 hover:text-purple-200 hover:bg-purple-500/10"
                        >
                            View Latest Scan
                            <ArrowRight className="ml-2 h-3 w-3" />
                        </Button>
                    </Link>
                )}
            </CardContent>
        </Card>
    );
}
