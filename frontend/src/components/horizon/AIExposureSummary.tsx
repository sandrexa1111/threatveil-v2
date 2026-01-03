'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, TrendingDown, TrendingUp, Minus, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';

interface AIExposureSummaryProps {
    score: number;
    trend: number;
    status: 'clean' | 'warning' | 'critical';
    summary?: string;
}

/**
 * AIExposureSummary - AI posture summary card for Horizon dashboard
 * 
 * Shows:
 * - Status badge (clean/warning/critical)
 * - AI risk score and trend
 * - Summary text
 */
export function AIExposureSummary({
    score,
    trend,
    status,
    summary = 'No AI exposure data available',
}: AIExposureSummaryProps) {
    const getStatusIcon = () => {
        switch (status) {
            case 'clean':
                return <ShieldCheck className="h-5 w-5 text-emerald-400" />;
            case 'warning':
                return <ShieldAlert className="h-5 w-5 text-yellow-400" />;
            case 'critical':
                return <ShieldX className="h-5 w-5 text-red-400" />;
        }
    };

    const getStatusBadgeStyle = () => {
        switch (status) {
            case 'clean':
                return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
            case 'warning':
                return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
            case 'critical':
                return 'bg-red-500/10 border-red-500/30 text-red-400';
        }
    };

    const getStatusLabel = () => {
        switch (status) {
            case 'clean':
                return 'Clean';
            case 'warning':
                return 'Warning';
            case 'critical':
                return 'Critical';
        }
    };

    const getTrendIcon = () => {
        if (trend < 0) return <TrendingDown className="h-3.5 w-3.5 text-emerald-400" />;
        if (trend > 0) return <TrendingUp className="h-3.5 w-3.5 text-red-400" />;
        return <Minus className="h-3.5 w-3.5 text-slate-400" />;
    };

    const getTrendText = () => {
        if (trend < 0) return `${trend}`;
        if (trend > 0) return `+${trend}`;
        return '±0';
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-400" />
                    AI Exposure
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between mb-3">
                    {/* Status and score */}
                    <div className="flex items-center gap-3">
                        {getStatusIcon()}
                        <div>
                            <Badge variant="outline" className={getStatusBadgeStyle()}>
                                {getStatusLabel()}
                            </Badge>
                        </div>
                    </div>

                    {/* Score with trend */}
                    <div className="text-right">
                        <div className="flex items-center gap-1.5">
                            <span className="text-2xl font-bold text-white">{score}</span>
                            <span className="text-sm text-slate-500">/100</span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-slate-400">
                            {getTrendIcon()}
                            <span>{getTrendText()} this week</span>
                        </div>
                    </div>
                </div>

                {/* Summary text */}
                <p className="text-sm text-slate-400 border-t border-slate-800 pt-3">
                    {summary}
                </p>
            </CardContent>
        </Card>
    );
}
