'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb, Target, Wrench, Loader2 } from 'lucide-react';

interface RiskReasoningPanelProps {
    businessImpact?: string;
    attackerMotivation?: string;
    priorityAction?: string;
    isLoading?: boolean;
}

/**
 * RiskReasoningPanel - Displays LLM-generated risk explanations
 * 
 * Shows three key insights:
 * - "What this means for your business"
 * - "Why attackers target this"
 * - "What to fix now"
 */
export function RiskReasoningPanel({
    businessImpact,
    attackerMotivation,
    priorityAction,
    isLoading = false,
}: RiskReasoningPanelProps) {
    if (isLoading) {
        return (
            <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <CardContent className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
                    <span className="ml-2 text-sm text-slate-400">Generating insights...</span>
                </CardContent>
            </Card>
        );
    }

    const insights = [
        {
            icon: Lightbulb,
            title: 'What this means for your business',
            content: businessImpact || 'Analysis not available. Run a scan to generate insights.',
            iconColor: 'text-amber-400',
            bgColor: 'bg-amber-500/10',
        },
        {
            icon: Target,
            title: 'Why attackers target this',
            content: attackerMotivation || 'No specific attack vectors identified.',
            iconColor: 'text-red-400',
            bgColor: 'bg-red-500/10',
        },
        {
            icon: Wrench,
            title: 'What to fix now',
            content: priorityAction || 'Complete a scan to receive prioritized recommendations.',
            iconColor: 'text-emerald-400',
            bgColor: 'bg-emerald-500/10',
        },
    ];

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-purple-400" />
                    Risk Intelligence
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {insights.map((insight, index) => {
                    const Icon = insight.icon;
                    return (
                        <div
                            key={index}
                            className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 transition-colors hover:border-slate-700"
                        >
                            <div className="flex items-start gap-3">
                                <div className={`rounded-lg p-2 ${insight.bgColor}`}>
                                    <Icon className={`h-4 w-4 ${insight.iconColor}`} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-medium text-slate-300 mb-1">
                                        {insight.title}
                                    </h4>
                                    <p className="text-sm text-slate-400 leading-relaxed">
                                        {insight.content}
                                    </p>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </CardContent>
        </Card>
    );
}
