'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { TagChip } from '@/components/TagChip';
import { Shield, Clock, Activity, Bug, GitBranch, Globe, ShieldAlert, Brain, Server, Database, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ScanResult, ScanAIResult } from '@/lib/types';
import { format } from 'date-fns';

interface ScanHeaderProps {
    scan: ScanResult;
    aiData?: ScanAIResult | null;
    isDemo?: boolean;
    previousScore?: number | null;  // Previous scan score for trend calculation
}

// All possible data sources with their metadata
const ALL_SOURCES = {
    'https': { icon: Globe, label: 'HTTP/S' },
    'http': { icon: Globe, label: 'HTTP' },
    'tls': { icon: Shield, label: 'TLS' },
    'dns': { icon: Server, label: 'DNS' },
    'ct': { icon: Database, label: 'CT Logs' },
    'vulners': { icon: Bug, label: 'Vulners' },
    'github': { icon: GitBranch, label: 'GitHub' },
    'otx': { icon: Activity, label: 'OTX' },
    'lakera': { icon: Brain, label: 'Lakera' },
    'ai_guard': { icon: ShieldAlert, label: 'AI Guard' },
} as const;

// Default enabled sources (configurable)
const ENABLED_SOURCES = ['https', 'tls', 'dns', 'vulners', 'github', 'otx'];

export function ScanHeader({ scan, aiData, isDemo = false, previousScore }: ScanHeaderProps) {
    // Extract unique sources from signals
    const usedSources = new Set(scan.signals.map(s => s.evidence.source));

    // Calculate trend if previous score exists
    const trend = previousScore !== null && previousScore !== undefined
        ? scan.risk_score - previousScore
        : null;

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                    <h1 className="text-3xl font-bold tracking-tight text-white/95">{scan.domain}</h1>
                    {isDemo && (
                        <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
                            Demo Data
                        </Badge>
                    )}
                    {/* Risk Trend Indicator */}
                    {trend !== null && (
                        <RiskTrendBadge trend={trend} />
                    )}
                </div>

                <div className="flex items-center gap-3 text-sm text-gray-400">
                    <span className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-gray-500" />
                        {format(new Date(scan.created_at), 'MMM d, yyyy • h:mm a')}
                    </span>
                    <span className="text-gray-600">|</span>
                    <span className="font-mono text-xs text-gray-500">{scan.id.slice(0, 8)}...</span>
                    <span className="text-gray-600">|</span>
                    <Badge variant="secondary" className="bg-gray-800 text-gray-400 hover:bg-gray-700 border-gray-700 font-normal text-xs px-2 py-0.5 h-5">
                        Passive scan only
                    </Badge>
                </div>
            </div>

            {/* Sources row with dot indicators */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs text-gray-500 font-medium mr-1 uppercase tracking-wider">Data Sources</span>
                {ENABLED_SOURCES.map((key) => {
                    const source = ALL_SOURCES[key as keyof typeof ALL_SOURCES];
                    if (!source) return null;

                    const isActive = usedSources.has(key);
                    const Icon = source.icon;

                    return (
                        <TagChip
                            key={key}
                            label={source.label}
                            icon={Icon}
                            isActive={isActive}
                            showDot={true}
                        />
                    );
                })}
            </div>
        </div>
    );
}

/**
 * Risk Trend Badge - Shows risk change since last scan.
 * Positive = worse (risk increased), Negative = better (risk reduced)
 */
function RiskTrendBadge({ trend }: { trend: number }) {
    if (trend === 0) {
        return (
            <Badge className="bg-gray-800 text-gray-400 border-gray-700 flex items-center gap-1">
                <Minus className="h-3 w-3" />
                <span className="text-xs">No change</span>
            </Badge>
        );
    }

    if (trend > 0) {
        // Risk increased - bad
        return (
            <Badge className="bg-red-500/10 text-red-400 border-red-500/20 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                <span className="text-xs">+{trend} pts</span>
            </Badge>
        );
    }

    // Risk decreased - good
    return (
        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            <span className="text-xs">{trend} pts</span>
        </Badge>
    );
}

