'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { ScanResult, ScanAIResult, SecurityDecision, DecisionStatus } from '@/lib/types';
import { getDecisions, generateDecisions, updateDecisionStatus } from '@/lib/api/scans';
import {
    Target, Clock, TrendingDown, ArrowRight, AlertTriangle,
    Key, Bug, Shield, Database, Globe, CheckCircle, Loader2, Play
} from 'lucide-react';

interface SecurityDecisionsCardProps {
    scan: ScanResult;
    aiData?: ScanAIResult | null;
}

// Icon mapping for action types
const ACTION_ICONS: Record<string, typeof Target> = {
    'key-rotation': Key,
    'patch-cves': Bug,
    'review-agents': AlertTriangle,
    'audit-data': Database,
    'update-tls': Shield,
    'review-network': Globe,
    'audit-ai-tools': Target,
};

// Status badge styling
const STATUS_STYLES: Record<DecisionStatus, { bg: string; text: string; label: string }> = {
    'pending': { bg: 'bg-amber-500/10', text: 'text-amber-400', label: 'Pending' },
    'accepted': { bg: 'bg-cyan-500/10', text: 'text-cyan-400', label: 'Accepted' },
    'in_progress': { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'In Progress' },
    'resolved': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', label: 'Resolved' },
    'verified': { bg: 'bg-emerald-500/10', text: 'text-emerald-300', label: 'Verified' },
};

export function SecurityDecisionsCard({ scan, aiData }: SecurityDecisionsCardProps) {
    const [decisions, setDecisions] = useState<SecurityDecision[]>([]);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState<string | null>(null);

    // Load or generate decisions on mount
    useEffect(() => {
        async function loadDecisions() {
            try {
                // First try to get existing decisions
                const result = await getDecisions(scan.id);
                if (result.decisions.length > 0) {
                    setDecisions(result.decisions);
                } else {
                    // Generate decisions if none exist
                    const generated = await generateDecisions(scan.id);
                    setDecisions(generated.decisions);
                }
            } catch (error) {
                console.error('Failed to load decisions:', error);
            } finally {
                setLoading(false);
            }
        }
        loadDecisions();
    }, [scan.id]);

    // Handle status change
    const handleStatusChange = async (decision: SecurityDecision, newStatus: DecisionStatus) => {
        setUpdating(decision.id);
        try {
            const result = await updateDecisionStatus(decision.id, newStatus);
            // Update local state
            setDecisions(prev => prev.map(d =>
                d.id === decision.id ? result.decision : d
            ));
        } catch (error) {
            console.error('Failed to update status:', error);
        } finally {
            setUpdating(null);
        }
    };

    // Separate pending/in_progress from resolved
    const activeDecisions = decisions.filter(d => d.status !== 'resolved');
    const resolvedDecisions = decisions.filter(d => d.status === 'resolved');

    // Loading state
    if (loading) {
        return (
            <div className="rounded-xl border-l-2 border-l-cyan-500/50 border border-slate-800/60 bg-[#111827]/80">
                <div className="py-12 flex items-center justify-center">
                    <Loader2 className="h-5 w-5 animate-spin text-cyan-500" />
                    <span className="ml-3 text-sm text-slate-400">Loading priorities...</span>
                </div>
            </div>
        );
    }

    // Empty state - no decisions needed
    if (decisions.length === 0) {
        return (
            <div className="rounded-xl border-l-2 border-l-cyan-500/50 border border-slate-800/60 bg-[#111827]/80">
                <div className="px-5 py-4 border-b border-slate-800/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Target className="h-4 w-4 text-cyan-400" />
                            <h3 className="text-sm font-semibold text-white">This Week&apos;s Priorities</h3>
                        </div>
                        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-xs">
                            All Clear
                        </Badge>
                    </div>
                </div>
                <div className="p-6">
                    <div className="text-center py-6">
                        <Shield className="h-10 w-10 text-emerald-500/40 mx-auto mb-3" />
                        <p className="text-base font-medium text-white/90 mb-1">Security posture is stable</p>
                        <p className="text-sm text-slate-500 max-w-xs mx-auto">
                            No urgent actions this week. We&apos;ll notify you when new priorities emerge.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // Calculate totals
    const totalPotentialReduction = activeDecisions.reduce((sum, d) => sum + d.estimated_risk_reduction, 0);
    const totalActualReduction = resolvedDecisions.reduce((sum, d) => {
        if (d.before_score !== null && d.after_score !== null) {
            return sum + (d.before_score - d.after_score);
        }
        return sum;
    }, 0);

    return (
        <div className="rounded-xl border-l-2 border-l-cyan-500/50 border border-slate-800/60 bg-[#111827]/80">
            {/* Header */}
            <div className="px-5 py-4 border-b border-slate-800/50">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2">
                            <Target className="h-4 w-4 text-cyan-400" />
                            <h3 className="text-sm font-semibold text-white">This Week&apos;s Priorities</h3>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                            {activeDecisions.length} pending • {resolvedDecisions.length} resolved
                            {totalPotentialReduction > 0 && ` • Up to ${totalPotentialReduction}% risk reduction`}
                        </p>
                    </div>
                    {totalActualReduction > 0 && (
                        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 flex items-center gap-1 text-xs">
                            <TrendingDown className="h-3 w-3" />
                            {totalActualReduction} pts reduced
                        </Badge>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="p-5 space-y-5">
                {/* Active Decisions */}
                {activeDecisions.length > 0 && (
                    <div className="space-y-3">
                        {activeDecisions.map((decision, index) => (
                            <DecisionItem
                                key={decision.id}
                                decision={decision}
                                index={index}
                                updating={updating === decision.id}
                                onStatusChange={handleStatusChange}
                            />
                        ))}
                    </div>
                )}

                {/* Resolved Decisions */}
                {resolvedDecisions.length > 0 && (
                    <div className="pt-4 border-t border-slate-800/50">
                        <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <CheckCircle className="h-3 w-3 text-emerald-500" />
                            Completed This Week
                        </p>
                        <div className="space-y-2">
                            {resolvedDecisions.map((decision) => (
                                <ResolvedDecisionItem
                                    key={decision.id}
                                    decision={decision}
                                    updating={updating === decision.id}
                                    onStatusChange={handleStatusChange}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Footer */}
                <p className="text-xs text-slate-600 pt-2">
                    Prioritized by exploit likelihood. Deterministic logic—no AI hallucinations.
                </p>
            </div>
        </div>
    );
}

// Active decision item with full details
function DecisionItem({
    decision,
    index,
    updating,
    onStatusChange
}: {
    decision: SecurityDecision;
    index: number;
    updating: boolean;
    onStatusChange: (decision: SecurityDecision, status: DecisionStatus) => void;
}) {
    const Icon = ACTION_ICONS[decision.action_id] || Target;
    const statusStyle = STATUS_STYLES[decision.status];

    return (
        <div className="group p-4 rounded-lg border border-slate-800/50 bg-slate-900/30 hover:bg-slate-900/50 transition-colors">
            <div className="flex items-start gap-3">
                {/* Priority number */}
                <div className="flex-shrink-0 h-7 w-7 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                    <span className="text-xs font-semibold text-cyan-400">{index + 1}</span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h4 className="text-sm font-medium text-white">{decision.title}</h4>
                        <Badge className={`${statusStyle.bg} ${statusStyle.text} text-xs border-0 px-1.5 py-0`}>
                            {statusStyle.label}
                        </Badge>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed mb-2">
                        {decision.recommended_fix}
                    </p>

                    {/* Metrics */}
                    <div className="flex items-center gap-4 text-xs">
                        <div className="flex items-center gap-1.5 text-emerald-400">
                            <TrendingDown className="h-3 w-3" />
                            <span className="font-medium">-{decision.estimated_risk_reduction}% risk</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-500">
                            <Clock className="h-3 w-3" />
                            <span>{decision.effort_estimate}</span>
                        </div>
                    </div>
                </div>

                {/* Action button */}
                <div className="flex-shrink-0">
                    {decision.status === 'pending' && (
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-blue-400 hover:bg-blue-500/10 hover:text-blue-300 h-8 w-8 p-0"
                            onClick={() => onStatusChange(decision, 'in_progress')}
                            disabled={updating}
                        >
                            {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                        </Button>
                    )}
                    {decision.status === 'in_progress' && (
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300 h-8 w-8 p-0"
                            onClick={() => onStatusChange(decision, 'resolved')}
                            disabled={updating}
                        >
                            {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Resolved decision item - compact view
function ResolvedDecisionItem({
    decision,
    updating,
    onStatusChange
}: {
    decision: SecurityDecision;
    updating: boolean;
    onStatusChange: (decision: SecurityDecision, status: DecisionStatus) => void;
}) {
    const riskDelta = decision.before_score !== null && decision.after_score !== null
        ? decision.before_score - decision.after_score
        : null;

    return (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
            <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
                <p className="text-sm text-emerald-200 font-medium truncate">{decision.title}</p>
                {riskDelta !== null && riskDelta > 0 && (
                    <p className="text-xs text-emerald-400/70 flex items-center gap-1 mt-0.5">
                        <TrendingDown className="h-3 w-3" />
                        Risk reduced by {riskDelta} points
                    </p>
                )}
            </div>
            <Button
                variant="ghost"
                size="sm"
                className="text-slate-500 hover:text-slate-300 text-xs h-7 px-2"
                onClick={() => onStatusChange(decision, 'pending')}
                disabled={updating}
            >
                {updating ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Undo'}
            </Button>
        </div>
    );
}
