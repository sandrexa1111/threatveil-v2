'use client';

import { motion } from 'framer-motion';
import { Check, X, AlertTriangle, Brain } from 'lucide-react';
import { Container } from '@/components/layout/Container';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const problems = [
    'Too many alerts, not enough context',
    'No prioritization—everything is "critical"',
    'Requires SOC expertise to interpret',
    'No business narrative for executives',
    'Designed for enterprises, priced for enterprises',
];

const solutions = [
    '3 prioritized actions per week',
    'Ranked by actual exploit likelihood',
    'Plain-English explanations anyone can understand',
    'Executive-ready weekly briefs',
    'Built and priced for teams of 10–500',
];

export function ComparisonSection() {
    return (
        <section id="comparison" className="bg-slate-950 py-24 md:py-32">
            <Container>
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
                        The Problem
                    </p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        Why security tools fail small teams
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        Traditional security products assume you have a SOC. You don&apos;t.
                    </p>
                </FadeIn>

                <div className="mx-auto max-w-5xl">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
                        {/* Problem Column */}
                        <FadeIn direction="right" delay={0.2} className="relative group">
                            <div className="absolute inset-0 bg-red-500/5 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                            <div className="relative h-full rounded-2xl border border-slate-800 bg-slate-900/50 p-8 hover:border-red-500/20 transition-colors duration-300">
                                <div className="mb-6 flex items-center gap-4 border-b border-slate-800/50 pb-6">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10 text-red-400 shadow-sm shadow-red-500/10">
                                        <AlertTriangle className="h-5 w-5" />
                                    </div>
                                    <h3 className="text-lg font-bold text-slate-200">Traditional Security Tools</h3>
                                </div>
                                <StaggerContainer className="space-y-4">
                                    {problems.map((problem, idx) => (
                                        <motion.li
                                            key={idx}
                                            variants={{ hidden: { opacity: 0, x: -10 }, visible: { opacity: 1, x: 0 } }}
                                            className="flex items-start gap-3 text-sm text-slate-400"
                                        >
                                            <X className="mt-0.5 h-4 w-4 text-red-400/80 flex-shrink-0" />
                                            <span>{problem}</span>
                                        </motion.li>
                                    ))}
                                </StaggerContainer>
                            </div>
                        </FadeIn>

                        {/* Solution Column */}
                        <FadeIn direction="left" delay={0.4} className="relative group">
                            <div className="absolute inset-0 bg-cyan-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                            <div className="relative h-full rounded-2xl border border-cyan-500/30 bg-[#0B1120] p-8 shadow-2xl hover:border-cyan-500/50 transition-colors duration-300">
                                <div className="mb-6 flex items-center gap-4 border-b border-slate-800/50 pb-6">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 shadow-[0_0_15px_-3px_rgba(34,211,238,0.3)]">
                                        <Brain className="h-5 w-5" />
                                    </div>
                                    <h3 className="text-lg font-bold text-white">ThreatVeil</h3>
                                </div>
                                <StaggerContainer className="space-y-4">
                                    {solutions.map((solution, idx) => (
                                        <motion.li
                                            key={idx}
                                            variants={{ hidden: { opacity: 0, x: 10 }, visible: { opacity: 1, x: 0 } }}
                                            className="flex items-start gap-3 text-sm text-slate-300"
                                        >
                                            <Check className="mt-0.5 h-4 w-4 text-cyan-400 flex-shrink-0" />
                                            <span>{solution}</span>
                                        </motion.li>
                                    ))}
                                </StaggerContainer>
                            </div>
                        </FadeIn>
                    </div>

                    {/* Positioning statement */}
                    <FadeIn delay={0.6} className="mt-16 text-center">
                        <p className="text-lg text-slate-400 max-w-2xl mx-auto bg-slate-900/50 rounded-full px-6 py-2 border border-slate-800/50 inline-block">
                            ThreatVeil is a <span className="text-white font-semibold text-cyan-400">decision system</span>, not a scanner.
                        </p>
                    </FadeIn>
                </div>
            </Container>
        </section>
    );
}
