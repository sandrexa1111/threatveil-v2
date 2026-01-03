'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, Globe, Bug, Database, Brain, Building } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Signal {
    id: string;
    type: string;
    detail: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: string;
}

interface SignalGroup {
    name: string;
    key: string;
    icon: LucideIcon;
    signals: Signal[];
    color: string;
}

interface GroupedSignalsProps {
    signals: Signal[];
    defaultExpanded?: string[];
}

const CATEGORY_MAP: Record<string, { name: string; icon: LucideIcon; color: string }> = {
    network: { name: 'External Security', icon: Globe, color: 'text-blue-400' },
    infrastructure: { name: 'External Security', icon: Globe, color: 'text-blue-400' },
    software: { name: 'Software & CVEs', icon: Bug, color: 'text-purple-400' },
    data_exposure: { name: 'Data Exposure', icon: Database, color: 'text-red-400' },
    data: { name: 'Data Exposure', icon: Database, color: 'text-red-400' },
    ai_integration: { name: 'AI Exposure', icon: Brain, color: 'text-amber-400' },
    ai: { name: 'AI Exposure', icon: Brain, color: 'text-amber-400' },
    identity: { name: 'Identity Risk', icon: Building, color: 'text-cyan-400' },
    vendor: { name: 'Vendor Risk', icon: Building, color: 'text-slate-400' },
};

const SEVERITY_COLORS: Record<string, string> = {
    critical: 'bg-red-500/10 text-red-400 border-red-500/30',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    low: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
};

function groupSignals(signals: Signal[]): SignalGroup[] {
    const groups: Record<string, Signal[]> = {};

    signals.forEach((signal) => {
        const categoryInfo = CATEGORY_MAP[signal.category] || CATEGORY_MAP.network;
        const key = categoryInfo.name;
        if (!groups[key]) {
            groups[key] = [];
        }
        groups[key].push(signal);
    });

    // Add empty Vendor Risk placeholder
    if (!groups['Vendor Risk']) {
        groups['Vendor Risk'] = [];
    }

    return Object.entries(groups).map(([name, signals]) => {
        const firstSignal = signals[0];
        const categoryInfo = firstSignal
            ? CATEGORY_MAP[firstSignal.category] || CATEGORY_MAP.network
            : CATEGORY_MAP.vendor;

        return {
            name,
            key: name.toLowerCase().replace(/\s+/g, '_'),
            icon: categoryInfo.icon,
            signals,
            color: categoryInfo.color,
        };
    }).sort((a, b) => b.signals.length - a.signals.length);
}

export function GroupedSignals({ signals, defaultExpanded = [] }: GroupedSignalsProps) {
    const groups = groupSignals(signals);
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
        new Set(defaultExpanded.length > 0 ? defaultExpanded : groups.filter(g => g.signals.length > 0).map(g => g.key))
    );

    const toggleGroup = (key: string) => {
        setExpandedGroups((prev) => {
            const next = new Set(prev);
            if (next.has(key)) {
                next.delete(key);
            } else {
                next.add(key);
            }
            return next;
        });
    };

    return (
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold text-white">
                    Key Findings
                </CardTitle>
                <p className="text-xs text-gray-500 mt-1">Grouped by risk category — expand to see details</p>
            </CardHeader>
            <CardContent className="space-y-2">
                {groups.map((group) => {
                    const Icon = group.icon;
                    const isExpanded = expandedGroups.has(group.key);
                    const isEmpty = group.signals.length === 0;

                    return (
                        <div key={group.key} className="rounded-lg border border-slate-800 overflow-hidden">
                            <button
                                onClick={() => !isEmpty && toggleGroup(group.key)}
                                disabled={isEmpty}
                                className={cn(
                                    "w-full flex items-center justify-between px-4 py-3 text-left transition-colors",
                                    isEmpty
                                        ? "bg-slate-900/30 cursor-not-allowed"
                                        : "bg-slate-900/50 hover:bg-slate-800/50 cursor-pointer"
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon className={cn("h-4 w-4", group.color)} />
                                    <span className="font-medium text-slate-200">{group.name}</span>
                                    <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
                                        {group.signals.length}
                                    </Badge>
                                </div>
                                {!isEmpty && (
                                    isExpanded
                                        ? <ChevronDown className="h-4 w-4 text-slate-500" />
                                        : <ChevronRight className="h-4 w-4 text-slate-500" />
                                )}
                                {isEmpty && (
                                    <span className="text-xs text-slate-500">Coming soon</span>
                                )}
                            </button>

                            {isExpanded && !isEmpty && (
                                <div className="border-t border-slate-800 divide-y divide-slate-800/50">
                                    {group.signals.map((signal) => (
                                        <div key={signal.id} className="px-4 py-3 bg-slate-950/50">
                                            <div className="flex items-start justify-between gap-3">
                                                <p className="text-sm text-slate-300 flex-1">{signal.detail}</p>
                                                <Badge
                                                    variant="outline"
                                                    className={cn("text-xs shrink-0", SEVERITY_COLORS[signal.severity])}
                                                >
                                                    {signal.severity}
                                                </Badge>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </CardContent>
        </Card>
    );
}
