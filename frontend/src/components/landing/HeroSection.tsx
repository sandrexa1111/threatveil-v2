'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Container } from '@/components/layout/Container';
import { ShieldAlert, ArrowRight, ChevronDown, CheckCircle2 } from 'lucide-react';
import { FadeIn, StaggerContainer, AmbientBackground } from '@/components/ui/motion-primitives';
import { cn } from '@/lib/utils';

export function HeroSection() {
    const [riskScore, setRiskScore] = useState(0);
    const [scanProgress, setScanProgress] = useState(0);
    const [isScanning, setIsScanning] = useState(true);

    const scrollToHowItWorks = () => {
        document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
    };

    // Simulate animated risk score count-up and scan line
    useEffect(() => {
        // Counter animation
        const interval = setInterval(() => {
            setRiskScore(prev => {
                if (prev >= 72) return 72;
                return prev + 1;
            });
        }, 30);

        // Progress bar animation
        const progressInterval = setInterval(() => {
            setScanProgress(prev => {
                if (prev >= 100) {
                    setIsScanning(false);
                    return 100;
                }
                return prev + 2;
            });
        }, 50);

        return () => {
            clearInterval(interval);
            clearInterval(progressInterval);
        };
    }, []);

    return (
        <section className="relative overflow-hidden bg-slate-950 pt-28 pb-20 md:pt-36 md:pb-32 min-h-[90vh] flex items-center">
            <AmbientBackground />

            <Container className="relative z-10">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:items-center">
                    {/* Left Column: Text */}
                    <div className="flex flex-col space-y-8">
                        <StaggerContainer>
                            <FadeIn delay={0.1}>
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="h-px w-8 bg-cyan-500/50" />
                                    <span className="text-xs font-semibold text-cyan-400 uppercase tracking-widest">
                                        AI Security Decision Platform
                                    </span>
                                </div>
                            </FadeIn>

                            <FadeIn delay={0.2}>
                                <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-[4rem] leading-[1.1]">
                                    Security decisions<br />
                                    <motion.span
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.8, duration: 0.8 }}
                                        className="text-slate-500"
                                    >
                                        that matter.
                                    </motion.span>
                                </h1>
                            </FadeIn>

                            <FadeIn delay={0.4}>
                                <p className="mt-6 text-lg leading-relaxed text-slate-400 max-w-lg">
                                    The AI-native decision platform for teams without a SOC.
                                    Turn noise into the <span className="text-white font-medium">3 actions</span> that measurably reduce breach risk this week.
                                </p>
                            </FadeIn>

                            <FadeIn delay={0.6}>
                                <div className="mt-8 flex flex-wrap gap-4">
                                    <Link href="/app">
                                        <Button size="lg" className="h-12 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-900 px-8 font-medium shadow-[0_0_20px_-5px_rgba(34,211,238,0.4)] hover:shadow-[0_0_25px_-5px_rgba(34,211,238,0.6)] transition-all">
                                            Start Free Scan
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </Link>
                                    <Button
                                        variant="ghost"
                                        size="lg"
                                        className="h-12 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
                                        onClick={scrollToHowItWorks}
                                    >
                                        See how it works
                                    </Button>
                                </div>
                            </FadeIn>

                            <FadeIn delay={0.8} className="mt-10 pt-8 border-t border-slate-800/50">
                                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
                                    Trusted by modern teams
                                </p>
                                <div className="flex flex-wrap gap-x-8 gap-y-3 opacity-60 grayscale transition-all hover:grayscale-0 hover:opacity-100">
                                    {/* Placeholders for logos - simplified text for now */}
                                    {['Acme Corp', 'Linear', 'Vercel', 'Ramp'].map((logo, i) => (
                                        <span key={i} className="text-sm font-semibold text-slate-300">{logo}</span>
                                    ))}
                                </div>
                            </FadeIn>
                        </StaggerContainer>
                    </div>

                    {/* Right Column: "Alive" Dashboard Preview */}
                    <FadeIn delay={0.4} direction="left" className="relative group">
                        {/* Glow behind the card */}
                        <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-2xl blur-xl opacity-30 group-hover:opacity-50 transition-opacity duration-1000" />

                        <div className="relative rounded-xl border border-slate-800 bg-[#0B1120]/90 backdrop-blur-xl p-6 shadow-2xl transform transition-transform duration-700 hover:scale-[1.01] hover:rotate-[0.5deg]">
                            {/* Header */}
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-cyan-400">
                                        <ShieldAlert className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-white text-sm">acme-corp.com</h3>
                                        <div className="flex items-center gap-2">
                                            <span className="relative flex h-2 w-2">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                                            </span>
                                            <p className="text-xs text-slate-400">
                                                {isScanning ? 'Determining Priorities...' : 'Analysis Complete'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-slate-500 mb-1">Risk Score</div>
                                    <div className={cn(
                                        "text-2xl font-bold font-mono transition-colors duration-500",
                                        riskScore > 50 ? "text-amber-400" : "text-emerald-400"
                                    )}>
                                        {riskScore}/100
                                    </div>
                                </div>
                            </div>

                            {/* Scan Line (only visible when scanning) */}
                            {isScanning && (
                                <div className="absolute top-24 left-0 w-full h-px bg-cyan-500/30 overflow-hidden">
                                    <motion.div
                                        className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]"
                                        initial={{ x: '-100%' }}
                                        animate={{ x: '100%' }}
                                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                                    />
                                </div>
                            )}

                            {/* Priorities List */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between text-xs text-slate-500 uppercase tracking-wider font-medium border-b border-slate-800/50 pb-2">
                                    <span>Weekly Priorities</span>
                                    <span>Risk Impact</span>
                                </div>

                                <StaggerContainer delay={1.5} staggerDelay={0.2}>
                                    {[
                                        { num: 1, text: "Rotate exposed OpenAI API key", reduction: -12, urgent: true, category: 'AI Security' },
                                        { num: 2, text: "Patch critical CVE-2024-4098", reduction: -8, category: 'Infrastructure' },
                                        { num: 3, text: "Enable MFA on admin portal", reduction: -4, category: 'Access' },
                                    ].map((item) => (
                                        <FadeIn key={item.num} direction="left" className="group/item">
                                            <div className="flex items-center gap-4 rounded-lg p-3 border border-transparent hover:border-slate-700/50 hover:bg-slate-800/30 transition-all cursor-default">
                                                <span className={cn(
                                                    "flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold transition-colors",
                                                    item.urgent ? 'bg-amber-500/10 text-amber-500 ring-1 ring-amber-500/20' : 'bg-slate-800 text-slate-400'
                                                )}>
                                                    {item.num}
                                                </span>
                                                <div className="flex-1">
                                                    <div className="text-sm text-slate-300 font-medium group-hover/item:text-white transition-colors">{item.text}</div>
                                                    <div className="text-[10px] text-slate-500 mt-0.5">{item.category}</div>
                                                </div>
                                                <div className="flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-500/5 px-2 py-1 rounded border border-emerald-500/10">
                                                    <ArrowRight className="h-3 w-3 rotate-45" />
                                                    {item.reduction}
                                                </div>
                                            </div>
                                        </FadeIn>
                                    ))}
                                </StaggerContainer>
                            </div>

                            {/* Floating "AI Analysis" Marker */}
                            <motion.div
                                className="absolute -right-4 top-1/2 bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl z-20"
                                initial={{ opacity: 0, scale: 0.8, x: 20 }}
                                animate={{ opacity: 1, scale: 1, x: 0 }}
                                transition={{ delay: 2.2, duration: 0.5 }}
                            >
                                <div className="flex items-center gap-2">
                                    <div className="h-2 w-2 rounded-full bg-purple-500 animate-pulse" />
                                    <span className="text-xs font-medium text-slate-300">Correlating GitHub & DNS...</span>
                                </div>
                            </motion.div>
                        </div>
                    </FadeIn>
                </div>
            </Container>
        </section>
    );
}
