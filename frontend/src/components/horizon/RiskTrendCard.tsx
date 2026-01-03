'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingDown, TrendingUp, Minus, AlertTriangle } from 'lucide-react';

interface RiskTrendCardProps {
    currentScore: number;
    trend: number;
    criticalSignals: number;
    lastUpdated?: string | null;
}

/**
 * RiskTrendCard - Visual display of current risk score and trend
 * 
 * Shows:
 * - Large current risk score
 * - Trend arrow and delta
 * - Critical signals count
 * - Last updated timestamp
 */
export function RiskTrendCard({
    currentScore,
    trend,
    criticalSignals,
    lastUpdated,
}: RiskTrendCardProps) {
    const getTrendIcon = () => {
        if (trend < 0) return <TrendingDown className="h-5 w-5 text-emerald-400" />;
        if (trend > 0) return <TrendingUp className="h-5 w-5 text-red-400" />;
        return <Minus className="h-5 w-5 text-slate-400" />;
    };

    const getTrendColor = () => {
        if (trend < 0) return 'text-emerald-400';
        if (trend > 0) return 'text-red-400';
        return 'text-slate-400';
    };

    const getTrendText = () => {
        if (trend < 0) return `${trend} from last week`;
        if (trend > 0) return `+${trend} from last week`;
        return 'No change';
    };

    const getScoreColor = () => {
        if (currentScore > 70) return 'text-red-400';
        if (currentScore > 40) return 'text-yellow-400';
        return 'text-emerald-400';
    };

    const getScoreBadgeStyle = () => {
        if (currentScore > 70) return 'bg-red-500/10 border-red-500/30 text-red-400';
        if (currentScore > 40) return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    };

    const formatDate = (dateStr: string | null | undefined) => {
        if (!dateStr) return 'Never';
        try {
            return new Date(dateStr).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
            });
        } catch {
            return 'Unknown';
        }
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider">
                    Organization Risk Score
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-baseline gap-4 mb-4">
                    {/* Large score display */}
                    <span className={`text-5xl font-bold ${getScoreColor()}`}>
                        {currentScore}
                    </span>
                    <span className="text-lg text-slate-500">/100</span>

                    {/* Trend badge */}
                    <div className={`flex items-center gap-1 ${getTrendColor()}`}>
                        {getTrendIcon()}
                        <span className="text-sm font-medium">{getTrendText()}</span>
                    </div>
                </div>

                {/* Stats row */}
                <div className="flex items-center justify-between border-t border-slate-800 pt-3">
                    {/* Critical signals */}
                    <div className="flex items-center gap-2">
                        {criticalSignals > 0 ? (
                            <>
                                <AlertTriangle className="h-4 w-4 text-red-400" />
                                <span className="text-sm text-slate-300">
                                    {criticalSignals} critical signal{criticalSignals !== 1 ? 's' : ''}
                                </span>
                            </>
                        ) : (
                            <Badge variant="outline" className={getScoreBadgeStyle()}>
                                No critical issues
                            </Badge>
                        )}
                    </div>

                    {/* Last updated */}
                    <span className="text-xs text-slate-500">
                        Updated {formatDate(lastUpdated)}
                    </span>
                </div>
            </CardContent>
        </Card>
    );
}
