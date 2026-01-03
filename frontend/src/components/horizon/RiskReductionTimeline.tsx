'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, TrendingDown, TrendingUp, Minus, BarChart3 } from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { getRiskTimeline } from '@/lib/api/scans';
import type { RiskTimelinePoint } from '@/lib/types';

interface RiskReductionTimelineProps {
    orgId: string;
    className?: string;
}

/**
 * RiskReductionTimeline - Phase 2 component showing weekly risk scores
 * 
 * Displays a line chart of weekly risk scores with:
 * - Current score and delta from previous week
 * - Interactive tooltips showing week details
 * - Visual trend indicators
 */
export function RiskReductionTimeline({
    orgId,
    className = '',
}: RiskReductionTimelineProps) {
    const [points, setPoints] = useState<RiskTimelinePoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchTimeline() {
            setIsLoading(true);
            setError(null);
            try {
                const timeline = await getRiskTimeline(orgId, 12);
                setPoints(timeline.points);
            } catch (err) {
                console.error('Failed to fetch risk timeline:', err);
                setError('Failed to load timeline');
            } finally {
                setIsLoading(false);
            }
        }

        fetchTimeline();
    }, [orgId]);

    // Get the latest point for summary
    const latestPoint = points[points.length - 1];
    const previousPoint = points[points.length - 2];

    const getDelta = () => {
        if (!latestPoint || !previousPoint) return null;
        return latestPoint.risk_score - previousPoint.risk_score;
    };

    const delta = getDelta();

    const getTrendIcon = () => {
        if (delta === null) return <Minus className="h-4 w-4 text-slate-400" />;
        if (delta < 0) return <TrendingDown className="h-4 w-4 text-emerald-400" />;
        if (delta > 0) return <TrendingUp className="h-4 w-4 text-red-400" />;
        return <Minus className="h-4 w-4 text-slate-400" />;
    };

    const getTrendColor = () => {
        if (delta === null) return 'text-slate-400';
        if (delta < 0) return 'text-emerald-400';
        if (delta > 0) return 'text-red-400';
        return 'text-slate-400';
    };

    const formatWeek = (weekStart: string) => {
        try {
            const date = new Date(weekStart);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return weekStart;
        }
    };

    // Custom tooltip component
    const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: RiskTimelinePoint }> }) => {
        if (!active || !payload || !payload[0]) return null;

        const point = payload[0].payload;
        return (
            <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 shadow-lg">
                <p className="text-xs text-slate-400 mb-1">
                    Week of {formatWeek(point.week_start)}
                </p>
                <p className="text-sm font-medium text-white">
                    Risk Score: {point.risk_score}
                </p>
                {point.ai_score !== null && (
                    <p className="text-xs text-purple-400">
                        AI Score: {point.ai_score}
                    </p>
                )}
                {point.delta_from_prev !== null && (
                    <p className={`text-xs ${point.delta_from_prev < 0 ? 'text-emerald-400' : point.delta_from_prev > 0 ? 'text-red-400' : 'text-slate-400'}`}>
                        {point.delta_from_prev > 0 ? '+' : ''}{point.delta_from_prev} from prev week
                    </p>
                )}
            </div>
        );
    };

    if (isLoading) {
        return (
            <Card className={`border-slate-800 bg-slate-900/50 backdrop-blur-sm ${className}`}>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Risk Reduction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-center h-[200px]">
                    <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
                </CardContent>
            </Card>
        );
    }

    if (error || points.length === 0) {
        return (
            <Card className={`border-slate-800 bg-slate-900/50 backdrop-blur-sm ${className}`}>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Risk Reduction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-center h-[200px]">
                    <p className="text-sm text-slate-500">
                        {error || 'No scan history available. Run scans to build your timeline.'}
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className={`border-slate-800 bg-slate-900/50 backdrop-blur-sm ${className}`}>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Risk Reduction Timeline
                    </CardTitle>

                    {/* Current score and trend */}
                    <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-white">
                            {latestPoint?.risk_score ?? '--'}
                        </span>
                        <span className="text-sm text-slate-500">/100</span>
                        {delta !== null && (
                            <div className={`flex items-center gap-1 ${getTrendColor()}`}>
                                {getTrendIcon()}
                                <span className="text-xs font-medium">
                                    {delta > 0 ? '+' : ''}{delta}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-[180px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                            data={points}
                            margin={{ top: 5, right: 5, left: -20, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="week_start"
                                tickFormatter={formatWeek}
                                tick={{ fontSize: 10, fill: '#64748b' }}
                                axisLine={{ stroke: '#334155' }}
                                tickLine={{ stroke: '#334155' }}
                            />
                            <YAxis
                                domain={[0, 100]}
                                tick={{ fontSize: 10, fill: '#64748b' }}
                                axisLine={{ stroke: '#334155' }}
                                tickLine={{ stroke: '#334155' }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Line
                                type="monotone"
                                dataKey="risk_score"
                                stroke="#a78bfa"
                                strokeWidth={2}
                                dot={{ fill: '#a78bfa', strokeWidth: 0, r: 3 }}
                                activeDot={{ fill: '#c4b5fd', strokeWidth: 0, r: 5 }}
                            />
                            {/* Optional AI score line */}
                            <Line
                                type="monotone"
                                dataKey="ai_score"
                                stroke="#f472b6"
                                strokeWidth={1}
                                strokeDasharray="4 4"
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                <p className="text-xs text-slate-600 text-center mt-2">
                    Showing last {points.length} weeks • Purple = Risk Score, Pink = AI Score
                </p>
            </CardContent>
        </Card>
    );
}
