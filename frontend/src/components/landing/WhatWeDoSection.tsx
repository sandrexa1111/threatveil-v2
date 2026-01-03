'use client';

import { motion } from 'framer-motion';
import { Container } from '@/components/layout/Container';
import { FeatureCard } from './LandingCards';
import { IconScan, IconIntelligence, IconTarget } from '@/components/ui/custom-icons';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const steps = [
    {
        icon: IconScan,
        title: 'Collect',
        description: 'We passively gather security intelligence from public sources—no agents, no credentials.',
        details: ['OSINT & Attack Surface', 'GitHub & Code Repos', 'DNS, TLS & CVEs', 'AI Tool Artifacts'],
    },
    {
        icon: IconIntelligence,
        title: 'Decide',
        description: 'Our deterministic engine models risk and generates AI-powered explanations for executives.',
        details: ['Weighted Risk Scoring', 'Exploit Likelihood', 'Business Impact Analysis', 'No AI Hallucinations'],
    },
    {
        icon: IconTarget,
        title: 'Act',
        description: 'Get 3 prioritized actions that reduce your breach risk this week—not 1,000 alerts.',
        details: ['Weekly Priorities Only', 'Effort Estimates', 'Risk Reduction Metrics', 'Plain-English Fixes'],
    },
];

export function WhatWeDoSection() {
    return (
        <section id="what-we-do" className="bg-slate-950 py-24 md:py-32 relative overflow-hidden">
            {/* Flow Line - Connecting the steps */}
            <div className="absolute top-[50%] left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent hidden md:block" />

            <Container className="relative z-10">
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
                        Not Just Another Scanner
                    </p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        What ThreatVeil actually does
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        We don&apos;t just find problems—we tell you what to fix this week.
                    </p>
                </FadeIn>

                <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
                    {steps.map((step, index) => (
                        <FadeIn key={index} delay={index * 0.1} className="relative">
                            {/* Connector Dot */}
                            <div className="absolute -top-[50px] left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-slate-900 border border-cyan-500/50 hidden md:block z-10">
                                <div className="absolute inset-0 bg-cyan-400/20 rounded-full animate-pulse" />
                            </div>

                            {/* Vertical Line to Card */}
                            <motion.div
                                className="absolute -top-[50px] left-1/2 w-px bg-cyan-500/20 h-[50px] hidden md:block"
                                initial={{ height: 0 }}
                                whileInView={{ height: 50 }}
                                transition={{ duration: 0.5, delay: 0.5 + (index * 0.2) }}
                            />

                            <FeatureCard
                                icon={step.icon}
                                title={step.title}
                                description={step.description}
                                details={step.details}
                                className="h-full bg-slate-900/40 border-slate-800/60"
                            />
                        </FadeIn>
                    ))}
                </StaggerContainer>
            </Container>
        </section>
    );
}
