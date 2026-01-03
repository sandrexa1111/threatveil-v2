'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getScan, getScanAI, getPreviousScan } from '@/lib/api/scans';
import { ScanResult, ScanAIResult } from '@/lib/types';
import { ScanHeader } from '@/components/ScanHeader';
import { RiskCard } from '@/components/RiskCard';
import { AIRiskPanel, AIRiskPanelLoading, AIRiskPanelError } from '@/components/AIRiskPanel';
import { SignalsTable } from '@/components/SignalsTable';
import { SecurityDecisionsCard } from '@/components/SecurityDecisionsCard';
import { SectionHeader, SkeletonCard, SkeletonStats } from '@/components/ui-kit';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowLeft, ShieldAlert, Download, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// Demo scan IDs for marketing/demo purposes
const DEMO_SCAN_IDS = new Set([
    'ae4bd793-b803-4c1a-b3a4-b1d2c7771116',
    'demo-scan-123',
    process.env.NEXT_PUBLIC_DEMO_SCAN_ID,
].filter(Boolean));

export default function ScanDetailPage() {
    const params = useParams();
    const id = params.id as string;

    const [scan, setScan] = useState<ScanResult | null>(null);
    const [aiData, setAiData] = useState<ScanAIResult | null | 'loading' | 'error'>('loading');
    const [previousScore, setPreviousScore] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const isDemo = DEMO_SCAN_IDS.has(id);

    // Detect if Lakera source is present in signals
    const hasLakera = scan?.signals.some(s =>
        s.evidence.source === 'lakera' || s.evidence.source === 'ai_guard'
    ) ?? false;

    useEffect(() => {
        if (!id) return;

        getScan(id)
            .then((data) => {
                setScan(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error(err);
                setError('Failed to load scan results. It might not exist or the backend is unreachable.');
                setLoading(false);
            });

        getScanAI(id)
            .then((data) => {
                setAiData(data);
            })
            .catch((err) => {
                console.error(err);
                setAiData('error');
            });

        // Fetch previous scan score for risk trend
        getPreviousScan(id)
            .then((data) => {
                setPreviousScore(data.previous_score);
            })
            .catch((err) => {
                console.error('Failed to fetch previous scan:', err);
            });
    }, [id]);

    const handleExportJSON = () => {
        if (!scan) return;

        const data = {
            ...scan,
            ai_data: aiData && aiData !== 'loading' && aiData !== 'error' ? aiData : null,
            exported_at: new Date().toISOString(),
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `threatveil-scan-${scan.domain}-${format(new Date(), 'yyyy-MM-dd')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Scan data exported');
    };

    // Loading state
    if (loading) {
        return (
            <div className="space-y-6 animate-fade-in">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-24 rounded bg-slate-800/60 animate-pulse" />
                </div>
                <SkeletonStats count={4} />
                <SkeletonCard />
                <div className="grid gap-6 lg:grid-cols-[60%_1fr]">
                    <SkeletonCard />
                    <SkeletonCard />
                </div>
            </div>
        );
    }

    // Error state
    if (error || !scan) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex h-[50vh] flex-col items-center justify-center gap-4"
            >
                <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20">
                    <AlertTriangle className="h-8 w-8 text-red-400" />
                </div>
                <p className="text-lg text-slate-300">{error || 'Scan not found'}</p>
                <Link href="/app/scans">
                    <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Scans
                    </Button>
                </Link>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
        >
            {/* Back button + Actions */}
            <div className="flex items-center justify-between">
                <Link href="/app/scans">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-slate-400 hover:text-white hover:bg-slate-800/50 -ml-2"
                    >
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Scans
                    </Button>
                </Link>

                <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExportJSON}
                    className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                    <Download className="h-4 w-4 mr-2" />
                    Export JSON
                </Button>
            </div>

            {/* Header with Risk Trend */}
            <ScanHeader
                scan={scan}
                aiData={aiData && aiData !== 'loading' && aiData !== 'error' ? aiData : undefined}
                isDemo={isDemo}
                previousScore={previousScore}
            />

            {/* Security Decisions Card - Top priority actions */}
            <SecurityDecisionsCard
                scan={scan}
                aiData={aiData && aiData !== 'loading' && aiData !== 'error' ? aiData : undefined}
            />

            {/* Main Grid: 60/40 split on desktop, stacked on mobile */}
            <div className="grid gap-6 lg:grid-cols-[60%_1fr] items-start">
                {/* Left: Cyber Risk (60%) */}
                <RiskCard result={scan} />

                {/* Right: AI Risk (40%) */}
                <div className="lg:sticky lg:top-24">
                    {aiData === 'loading' && <AIRiskPanelLoading scanId={scan.id} />}
                    {aiData === 'error' && <AIRiskPanelError />}
                    {aiData && aiData !== 'loading' && aiData !== 'error' && (
                        <AIRiskPanel
                            aiScore={aiData.ai_score}
                            aiSummary={aiData.ai_summary || ''}
                            tools={aiData.ai_tools_detected || []}
                            agents={aiData.ai_agents_detected || []}
                            leaks={aiData.ai_key_leaks || []}
                            hasLakera={hasLakera}
                            scanId={scan.id}
                        />
                    )}
                </div>
            </div>

            {/* Key Findings Table */}
            <div className="rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm p-6">
                <SectionHeader
                    title="Key Findings"
                    icon={ShieldAlert}
                    subtitle={`${scan.signals.length} signals detected`}
                    className="mb-6"
                />
                <SignalsTable signals={scan.signals} />
            </div>
        </motion.div>
    );
}
