'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Target, Clock, TrendingDown, ArrowRight, Shield } from 'lucide-react';
import type { DecisionSummary } from '@/lib/types';
import Link from 'next/link';

interface TopDecisionsListProps {
    decisions: DecisionSummary[];
    linkToScan?: string;
}

// Status badge styling
const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
    'pending': { bg: 'bg-yellow-500/10', text: 'text-yellow-400', label: 'Pending' },
    'in_progress': { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'In Progress' },
    'resolved': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', label: 'Resolved' },
};

/**
 * TopDecisionsList - Priority action list for Horizon dashboard
 * 
 * Shows:
 * - Top pending/in-progress decisions
 * - Priority numbers
 * - Risk reduction and effort estimates
 * - Link to detailed scan view
 */
export function TopDecisionsList({
    decisions,
    linkToScan,
}: TopDecisionsListProps) {
    if (decisions.length === 0) {
        return (
            <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Target className="h-4 w-4 text-purple-400" />
                        Top Priority Actions
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <Shield className="h-12 w-12 text-emerald-500/30 mx-auto mb-3" />
                        <p className="text-sm font-medium text-white/80 mb-1">No Urgent Actions</p>
                        <p className="text-xs text-slate-500">
                            Your security posture is looking good
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Target className="h-4 w-4 text-purple-400" />
                        Top Priority Actions
                    </CardTitle>
                    {linkToScan && (
                        <Link href={linkToScan}>
                            <Button variant="ghost" size="sm" className="text-purple-400 hover:text-purple-300">
                                View All <ArrowRight className="ml-1 h-3 w-3" />
                            </Button>
                        </Link>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {decisions.map((decision, index) => {
                    const statusStyle = STATUS_STYLES[decision.status] || STATUS_STYLES['pending'];

                    return (
                        <div
                            key={decision.id}
                            className="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
                        >
                            {/* Priority number */}
                            <div className="flex-shrink-0 h-7 w-7 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                                <span className="text-sm font-bold text-purple-400">{index + 1}</span>
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1 flex-wrap">
                                    <h4 className="text-sm font-medium text-white truncate">{decision.title}</h4>
                                    <Badge className={`${statusStyle.bg} ${statusStyle.text} text-xs border-0`}>
                                        {statusStyle.label}
                                    </Badge>
                                </div>

                                {/* Metrics row */}
                                <div className="flex items-center gap-4 text-xs">
                                    <div className="flex items-center gap-1 text-emerald-400">
                                        <TrendingDown className="h-3 w-3" />
                                        <span className="font-medium">-{decision.estimated_risk_reduction}% risk</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-slate-500">
                                        <Clock className="h-3 w-3" />
                                        <span>{decision.effort_estimate}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {/* Summary footer */}
                <p className="text-xs text-slate-600 text-center pt-2">
                    Prioritized by exploit likelihood and business impact
                </p>
            </CardContent>
        </Card>
    );
}
