'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { SectionHeader, EmptyState, SeverityBadge, LoadingSkeleton, SkeletonTable } from '@/components/ui-kit';
import { getRecentScans, RecentScan, deleteScan, removeRecentScan } from '@/lib/api/scans';
import {
    Activity, Plus, Clock, Globe, ExternalLink, Trash2,
    Filter, Download, ChevronRight, Brain, TrendingDown, TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

type RiskFilter = 'all' | 'high' | 'medium' | 'low';

export default function ScansPage() {
    const router = useRouter();
    const [scans, setScans] = useState<RecentScan[]>([]);
    const [selectedScan, setSelectedScan] = useState<RecentScan | null>(null);
    const [loading, setLoading] = useState(true);
    const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');

    useEffect(() => {
        const recentScans = getRecentScans();
        setScans(recentScans);
        if (recentScans.length > 0) {
            setSelectedScan(recentScans[0]);
        }
        setLoading(false);
    }, []);

    // Filtered scans based on risk level
    const filteredScans = useMemo(() => {
        if (riskFilter === 'all') return scans;

        return scans.filter(scan => {
            if (riskFilter === 'high') return scan.risk_score >= 70;
            if (riskFilter === 'medium') return scan.risk_score >= 30 && scan.risk_score < 70;
            if (riskFilter === 'low') return scan.risk_score < 30;
            return true;
        });
    }, [scans, riskFilter]);

    const getRiskLevel = (score: number): 'high' | 'medium' | 'low' => {
        if (score >= 70) return 'high';
        if (score >= 30) return 'medium';
        return 'low';
    };

    const getAIScore = (riskScore: number) => {
        return Math.min(Math.round(riskScore * 0.8), 100);
    };

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();

        if (!confirm('Are you sure you want to delete this scan?')) {
            return;
        }

        try {
            const updatedScans = scans.filter(s => s.id !== id);
            setScans(updatedScans);

            if (selectedScan?.id === id) {
                setSelectedScan(updatedScans.length > 0 ? updatedScans[0] : null);
            }

            removeRecentScan(id);
            await deleteScan(id);
            toast.success('Scan deleted');
        } catch (error) {
            console.error('Failed to delete scan:', error);
            toast.error('Failed to delete scan');
            const recent = getRecentScans();
            setScans(recent);
        }
    };

    const handleExportJSON = () => {
        const data = scans.map(s => ({
            id: s.id,
            domain: s.domain,
            risk_score: s.risk_score,
            created_at: s.created_at,
        }));

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `threatveil-scans-${format(new Date(), 'yyyy-MM-dd')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Scans exported');
    };

    // Loading state
    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div className="space-y-2">
                        <LoadingSkeleton variant="text" className="h-7 w-40" />
                        <LoadingSkeleton variant="text" className="h-4 w-64" />
                    </div>
                    <LoadingSkeleton variant="badge" className="h-9 w-32" />
                </div>
                <SkeletonTable rows={5} columns={5} />
            </div>
        );
    }

    // Filter counts for badges
    const filterCounts = {
        all: scans.length,
        high: scans.filter(s => s.risk_score >= 70).length,
        medium: scans.filter(s => s.risk_score >= 30 && s.risk_score < 70).length,
        low: scans.filter(s => s.risk_score < 30).length,
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                        <Activity className="h-6 w-6 text-cyan-400" />
                        Risk Assessments
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">
                        {scans.length} domain{scans.length !== 1 ? 's' : ''} analyzed
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {scans.length > 0 && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleExportJSON}
                            className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Export
                        </Button>
                    )}
                    <Link href="/app">
                        <Button className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium">
                            <Plus className="h-4 w-4 mr-2" />
                            New Scan
                        </Button>
                    </Link>
                </div>
            </div>

            {scans.length > 0 ? (
                <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
                    {/* Main Table */}
                    <div className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
                        {/* Filters */}
                        <div className="flex items-center gap-2 p-4 border-b border-slate-800/50 bg-slate-900/30">
                            <Filter className="h-4 w-4 text-slate-500" />
                            <span className="text-xs font-medium text-slate-400 mr-2">Risk Level:</span>
                            {(['all', 'high', 'medium', 'low'] as RiskFilter[]).map((filter) => (
                                <Button
                                    key={filter}
                                    variant={riskFilter === filter ? 'secondary' : 'ghost'}
                                    size="sm"
                                    onClick={() => setRiskFilter(filter)}
                                    className={cn(
                                        'h-7 text-xs font-medium capitalize transition-all',
                                        riskFilter === filter
                                            ? 'bg-slate-700 text-white'
                                            : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                                    )}
                                >
                                    {filter}
                                    {filter !== 'all' && (
                                        <span className={cn(
                                            'ml-1.5 px-1.5 py-0.5 rounded text-2xs',
                                            filter === 'high' && 'bg-red-500/20 text-red-400',
                                            filter === 'medium' && 'bg-amber-500/20 text-amber-400',
                                            filter === 'low' && 'bg-emerald-500/20 text-emerald-400'
                                        )}>
                                            {filterCounts[filter]}
                                        </span>
                                    )}
                                </Button>
                            ))}
                        </div>

                        {/* Table */}
                        <Table>
                            <TableHeader className="bg-slate-900/50">
                                <TableRow className="border-slate-800/50 hover:bg-transparent">
                                    <TableHead className="text-slate-400 font-medium">Domain</TableHead>
                                    <TableHead className="text-slate-400 font-medium w-[100px]">Risk</TableHead>
                                    <TableHead className="text-slate-400 font-medium w-[100px]">AI Exposure</TableHead>
                                    <TableHead className="text-slate-400 font-medium w-[120px]">Scanned</TableHead>
                                    <TableHead className="text-slate-400 font-medium w-[80px] text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <AnimatePresence mode="popLayout">
                                    {filteredScans.map((scan) => (
                                        <motion.tr
                                            key={scan.id}
                                            layout
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -10 }}
                                            className={cn(
                                                'border-slate-800/30 cursor-pointer transition-colors group',
                                                selectedScan?.id === scan.id
                                                    ? 'bg-cyan-500/5'
                                                    : 'hover:bg-white/[0.02]'
                                            )}
                                            onClick={() => setSelectedScan(scan)}
                                        >
                                            <TableCell className="py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-9 w-9 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-center group-hover:border-slate-600/50 transition-colors">
                                                        <Globe className="h-4 w-4 text-slate-400" />
                                                    </div>
                                                    <div>
                                                        <span className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                                                            {scan.domain}
                                                        </span>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-lg font-bold text-slate-300">{scan.risk_score}</span>
                                                    <SeverityBadge severity={getRiskLevel(scan.risk_score)} size="xs" showIcon={false} />
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4">
                                                <div className="flex items-center gap-1.5">
                                                    <Brain className="h-3.5 w-3.5 text-purple-400/70" />
                                                    <span className="text-sm text-slate-400">{getAIScore(scan.risk_score)}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4 text-xs text-slate-500">
                                                <div className="flex items-center gap-1.5">
                                                    <Clock className="h-3 w-3" />
                                                    {format(new Date(scan.created_at), 'MMM d, h:mm a')}
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4 text-right">
                                                <div className="flex items-center justify-end gap-1">
                                                    <Link href={`/app/scans/${scan.id}`} onClick={(e) => e.stopPropagation()}>
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-7 w-7 p-0 text-slate-500 hover:text-cyan-400"
                                                        >
                                                            <ExternalLink className="h-4 w-4" />
                                                        </Button>
                                                    </Link>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-7 w-7 p-0 text-slate-500 hover:text-red-400"
                                                        onClick={(e) => handleDelete(e, scan.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            </TableBody>
                        </Table>

                        {filteredScans.length === 0 && (
                            <div className="p-8 text-center">
                                <Filter className="h-10 w-10 text-slate-700 mx-auto mb-3" />
                                <p className="text-sm text-slate-400">No scans match the selected filter</p>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setRiskFilter('all')}
                                    className="mt-2 text-cyan-400 hover:text-cyan-300"
                                >
                                    Clear filter
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Selected Scan Summary */}
                    <div className="hidden lg:block">
                        {selectedScan ? (
                            <motion.div
                                key={selectedScan.id}
                                initial={{ opacity: 0, x: 10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm p-5 space-y-5 sticky top-24"
                            >
                                <SectionHeader
                                    title="Selected Scan"
                                    icon={Activity}
                                    size="sm"
                                />

                                <div className="space-y-4">
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Domain</p>
                                        <p className="text-lg font-semibold text-white">{selectedScan.domain}</p>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/50">
                                            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Risk Score</p>
                                            <div className="flex items-center gap-2">
                                                <span className="text-2xl font-bold text-white">{selectedScan.risk_score}</span>
                                                <SeverityBadge severity={getRiskLevel(selectedScan.risk_score)} size="sm" />
                                            </div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/50">
                                            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">AI Exposure</p>
                                            <div className="flex items-center gap-2">
                                                <span className="text-2xl font-bold text-purple-400">{getAIScore(selectedScan.risk_score)}</span>
                                                <Brain className="h-4 w-4 text-purple-400/60" />
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Scanned</p>
                                        <p className="text-sm text-slate-300 flex items-center gap-1.5">
                                            <Clock className="h-3.5 w-3.5" />
                                            {format(new Date(selectedScan.created_at), 'MMM d, yyyy • h:mm a')}
                                        </p>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-slate-800/50">
                                    <Link href={`/app/scans/${selectedScan.id}`}>
                                        <Button className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium">
                                            View Full Report
                                            <ChevronRight className="h-4 w-4 ml-2" />
                                        </Button>
                                    </Link>
                                </div>
                            </motion.div>
                        ) : (
                            <div className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm p-8 text-center">
                                <Activity className="h-10 w-10 text-slate-700 mx-auto mb-3" />
                                <p className="text-sm text-slate-500">Select a scan to view summary</p>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                // Empty state
                <EmptyState
                    icon="shield"
                    title="No assessments yet"
                    description="Start by running your first risk assessment to see what matters and what to fix first."
                    action={{
                        label: 'Run First Assessment',
                        href: '/app',
                    }}
                />
            )}
        </div>
    );
}
