'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import {
    TrendingDown,
    TrendingUp,
    Minus,
    AlertCircle,
    Loader2,
    RefreshCw
} from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { getDecisionImpact } from '@/lib/api/scans';
import type { DecisionImpactDetail } from '@/lib/types';

interface ImpactBadgeProps {
    decisionId: string;
    status: string;
    /** Callback when "Re-scan" CTA is clicked */
    onRescanClick?: () => void;
    className?: string;
}

/**
 * ImpactBadge - Phase 2 component showing decision impact
 * 
 * Displays:
 * - Delta badge (↓ 12 pts green, ↑ 4 pts red, — if unknown)
 * - Tooltip with confidence level
 * - Warning icon for low confidence (< 0.5)
 * - "Re-scan to measure impact" CTA if no after scan
 */
export function ImpactBadge({
    decisionId,
    status,
    onRescanClick,
    className = '',
}: ImpactBadgeProps) {
    const [impact, setImpact] = useState<DecisionImpactDetail | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Only fetch impact for resolved decisions
        if (status !== 'resolved') {
            return;
        }

        async function fetchImpact() {
            setIsLoading(true);
            setError(null);
            try {
                const data = await getDecisionImpact(decisionId);
                setImpact(data);
            } catch (err) {
                console.error('Failed to fetch decision impact:', err);
                setError('Failed to load impact');
            } finally {
                setIsLoading(false);
            }
        }

        fetchImpact();
    }, [decisionId, status]);

    // Not resolved - don't show anything
    if (status !== 'resolved') {
        return null;
    }

    // Loading state
    if (isLoading) {
        return (
            <Badge variant="outline" className={`border-slate-700 text-slate-400 ${className}`}>
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                Loading...
            </Badge>
        );
    }

    // Error or no impact data
    if (error || !impact) {
        return (
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Badge variant="outline" className={`border-slate-700 text-slate-500 ${className}`}>
                            <Minus className="h-3 w-3 mr-1" />
                            —
                        </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="text-xs">Impact not yet measured</p>
                        {onRescanClick && (
                            <Button
                                size="sm"
                                variant="ghost"
                                className="mt-1 h-6 text-xs text-purple-400 hover:text-purple-300"
                                onClick={onRescanClick}
                            >
                                <RefreshCw className="h-3 w-3 mr-1" />
                                Re-scan to measure
                            </Button>
                        )}
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    // Get badge styling based on delta
    const getBadgeStyles = () => {
        if (impact.delta === null) {
            return { bg: 'border-slate-700 text-slate-400', icon: <Minus className="h-3 w-3 mr-1" /> };
        }
        if (impact.delta < 0) {
            // Improvement (score went down)
            return {
                bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
                icon: <TrendingDown className="h-3 w-3 mr-1" />
            };
        }
        if (impact.delta > 0) {
            // Regression (score went up)
            return {
                bg: 'bg-red-500/10 border-red-500/30 text-red-400',
                icon: <TrendingUp className="h-3 w-3 mr-1" />
            };
        }
        return { bg: 'border-slate-700 text-slate-400', icon: <Minus className="h-3 w-3 mr-1" /> };
    };

    const { bg, icon } = getBadgeStyles();

    // Format delta display
    const formatDelta = () => {
        if (impact.delta === null) return '—';
        if (impact.delta < 0) return `↓ ${Math.abs(impact.delta)} pts`;
        if (impact.delta > 0) return `↑ ${impact.delta} pts`;
        return '0 pts';
    };

    // Get confidence label
    const getConfidenceLabel = () => {
        if (impact.confidence >= 0.9) return 'High';
        if (impact.confidence >= 0.6) return 'Medium';
        if (impact.confidence >= 0.4) return 'Low';
        return 'Very Low';
    };

    const isLowConfidence = impact.confidence < 0.5;

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Badge variant="outline" className={`${bg} ${className} cursor-help`}>
                        {icon}
                        {formatDelta()}
                        {isLowConfidence && (
                            <AlertCircle className="h-3 w-3 ml-1 text-yellow-500" />
                        )}
                    </Badge>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                    <div className="space-y-1">
                        <p className="text-sm font-medium">
                            Measured change after fix
                        </p>
                        <p className="text-xs text-slate-400">
                            Before: {impact.risk_before} → After: {impact.risk_after ?? 'N/A'}
                        </p>
                        <p className="text-xs text-slate-400">
                            Confidence: {getConfidenceLabel()} ({(impact.confidence * 100).toFixed(0)}%)
                        </p>
                        {impact.notes && (
                            <p className="text-xs text-yellow-400 mt-1">
                                ⚠️ {impact.notes}
                            </p>
                        )}
                        {isLowConfidence && onRescanClick && (
                            <Button
                                size="sm"
                                variant="ghost"
                                className="mt-2 h-6 text-xs text-purple-400 hover:text-purple-300 p-0"
                                onClick={onRescanClick}
                            >
                                <RefreshCw className="h-3 w-3 mr-1" />
                                Re-scan for higher confidence
                            </Button>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
