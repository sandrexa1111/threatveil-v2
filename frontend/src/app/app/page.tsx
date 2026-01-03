'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
    Search, Loader2, ArrowRight, Shield, Globe, Brain,
    Activity, ChevronRight, Clock, Zap
} from 'lucide-react';
import { createScan, getRecentScans, RecentScan } from '@/lib/api/scans';
import { toast } from 'sonner';
import { SectionHeader, StatCard, SeverityBadge, EmptyState } from '@/components/ui-kit';
import { DailyBriefCard } from '@/components/DailyBriefCard';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
    const router = useRouter();
    const [domain, setDomain] = useState('');
    const [loading, setLoading] = useState(false);
    const [recentScans, setRecentScans] = useState<RecentScan[]>([]);

    useEffect(() => {
        setRecentScans(getRecentScans());
    }, []);

    const handleScan = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!domain) return;

        setLoading(true);
        try {
            const result = await createScan({ domain });
            toast.success('Scan completed successfully');
            router.push(`/app/scans/${result.id}`);
        } catch (error) {
            toast.error('Failed to start scan. Please try again.');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const getRiskLevel = (score: number): 'high' | 'medium' | 'low' => {
        if (score >= 70) return 'high';
        if (score >= 30) return 'medium';
        return 'low';
    };

    const getAIScore = (riskScore: number) => {
        return Math.min(Math.round(riskScore * 0.8), 100);
    };

    // Stats from recent scans
    const avgRiskScore = recentScans.length > 0
        ? Math.round(recentScans.reduce((sum, s) => sum + s.risk_score, 0) / recentScans.length)
        : 0;

    const highRiskCount = recentScans.filter(s => s.risk_score >= 70).length;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
        >
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-cyan-500/10">
                        <Zap className="h-6 w-6 text-cyan-400" />
                    </div>
                    Security Brain
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                    Unified risk intelligence powered by AI. Scan, analyze, and act.
                </p>
            </div>

            {/* Quick Stats */}
            {recentScans.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <StatCard
                        label="Domains Scanned"
                        value={recentScans.length}
                        icon={Globe}
                        variant="default"
                    />
                    <StatCard
                        label="Avg. Risk Score"
                        value={avgRiskScore}
                        icon={Shield}
                        variant={avgRiskScore >= 70 ? 'danger' : avgRiskScore >= 30 ? 'warning' : 'success'}
                    />
                    <StatCard
                        label="High Risk Domains"
                        value={highRiskCount}
                        icon={Activity}
                        variant={highRiskCount > 0 ? 'danger' : 'success'}
                    />
                    <StatCard
                        label="AI Exposure Avg"
                        value={`${Math.round(recentScans.reduce((sum, s) => sum + getAIScore(s.risk_score), 0) / recentScans.length)}`}
                        icon={Brain}
                        variant="accent"
                    />
                </div>
            )}

            <div className="grid gap-6 lg:grid-cols-7">
                {/* Left Column: Scan Form + Recent Activity */}
                <div className="lg:col-span-4 space-y-6">
                    {/* Scan Form Card */}
                    <div className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-800/50">
                            <SectionHeader
                                title="New Risk Assessment"
                                icon={Search}
                                subtitle="Enter a domain to analyze external risks and AI exposures"
                            />
                        </div>
                        <div className="p-6">
                            <form onSubmit={handleScan} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="domain" className="text-slate-300 text-sm">
                                        Domain
                                    </Label>
                                    <div className="flex gap-3">
                                        <div className="relative flex-1">
                                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                                            <Input
                                                id="domain"
                                                placeholder="example.com"
                                                value={domain}
                                                onChange={(e) => setDomain(e.target.value)}
                                                disabled={loading}
                                                className={cn(
                                                    'pl-10 h-11 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500',
                                                    'focus-visible:ring-cyan-500 focus-visible:border-cyan-500/50'
                                                )}
                                            />
                                        </div>
                                        <Button
                                            type="submit"
                                            disabled={loading || !domain.trim()}
                                            className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium h-11 px-6"
                                        >
                                            {loading ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Analyzing
                                                </>
                                            ) : (
                                                <>
                                                    <Search className="mr-2 h-4 w-4" />
                                                    Analyze
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                                <p className="text-xs text-slate-500">
                                    We use passive OSINT signals only. No intrusive scanning.
                                </p>
                            </form>
                        </div>
                    </div>

                    {/* Recent Scans */}
                    <div className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-800/50">
                            <SectionHeader
                                title="Recent Assessments"
                                icon={Activity}
                                subtitle={`${recentScans.length} domain${recentScans.length !== 1 ? 's' : ''} analyzed`}
                                action={
                                    recentScans.length > 0 && (
                                        <Link href="/app/scans">
                                            <Button variant="ghost" size="sm" className="text-cyan-400 hover:text-cyan-300 h-7">
                                                View all
                                                <ChevronRight className="h-4 w-4 ml-1" />
                                            </Button>
                                        </Link>
                                    )
                                }
                            />
                        </div>
                        <div className="p-4">
                            {recentScans.length === 0 ? (
                                <EmptyState
                                    variant="compact"
                                    icon="shield"
                                    title="No assessments yet"
                                    description="Start by analyzing a domain above to see your security posture."
                                />
                            ) : (
                                <div className="rounded-lg border border-slate-800/50 overflow-hidden">
                                    <Table>
                                        <TableHeader className="bg-slate-900/50">
                                            <TableRow className="border-slate-800/50 hover:bg-transparent">
                                                <TableHead className="text-slate-400 font-medium">Domain</TableHead>
                                                <TableHead className="text-slate-400 font-medium w-[100px]">Risk</TableHead>
                                                <TableHead className="text-slate-400 font-medium w-[80px]">AI</TableHead>
                                                <TableHead className="w-[40px]"></TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {recentScans.slice(0, 5).map((scan) => (
                                                <TableRow
                                                    key={scan.id}
                                                    className="cursor-pointer border-slate-800/30 hover:bg-white/[0.02] transition-colors"
                                                    onClick={() => router.push(`/app/scans/${scan.id}`)}
                                                >
                                                    <TableCell className="py-3">
                                                        <div className="flex items-center gap-3">
                                                            <div className="h-8 w-8 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-center">
                                                                <Globe className="h-4 w-4 text-slate-400" />
                                                            </div>
                                                            <div>
                                                                <p className="text-sm font-medium text-slate-200">{scan.domain}</p>
                                                                <p className="text-2xs text-slate-500 flex items-center gap-1">
                                                                    <Clock className="h-3 w-3" />
                                                                    {format(new Date(scan.created_at), 'MMM d, h:mm a')}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="py-3">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-lg font-bold text-slate-300">{scan.risk_score}</span>
                                                            <SeverityBadge severity={getRiskLevel(scan.risk_score)} size="xs" showIcon={false} />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="py-3">
                                                        <div className="flex items-center gap-1.5">
                                                            <Brain className="h-3.5 w-3.5 text-purple-400/70" />
                                                            <span className="text-sm text-slate-400">{getAIScore(scan.risk_score)}</span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="py-3">
                                                        <ArrowRight className="h-4 w-4 text-slate-500" />
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Daily Brief */}
                <div className="lg:col-span-3">
                    <DailyBriefCard
                        topSignals={[]}
                        topActions={[
                            "Review critical signals from recent scans",
                            "Update security headers on exposed domains",
                            "Audit AI API keys and rotate if necessary",
                        ]}
                        riskDelta={0}
                        aiExposure="low"
                        lastScanId={recentScans[0]?.id || null}
                    />
                </div>
            </div>
        </motion.div>
    );
}
