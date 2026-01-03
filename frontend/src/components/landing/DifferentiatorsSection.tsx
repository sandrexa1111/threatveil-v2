'use client';

import { motion } from 'framer-motion';
import { Container } from '@/components/layout/Container';
import { FeatureCard } from './LandingCards';
import { IconIntelligence, IconTarget, IconScan, IconLock } from '@/components/ui/custom-icons';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const differentiators = [
    {
        icon: IconIntelligence,
        title: 'AI for Decisions, Not Detection',
        description: 'Most tools use AI to find threats. We use it to explain which ones matter and why—in business language.',
        accent: true,
    },
    {
        icon: IconTarget,
        title: 'Deterministic Scoring',
        description: 'Your risk score is calculated with transparent logic. No black boxes, no hallucinations—every number is auditable.',
    },
    {
        icon: IconScan,
        title: 'AI Risk Visibility',
        description: 'See exposed API keys, shadow AI tools, and agent frameworks. We scan for risks that didn\'t exist 2 years ago.',
    },
    {
        icon: IconLock,
        title: 'Executive-Ready Outputs',
        description: 'Weekly briefs your CEO can understand. Risk reduction you can prove. Decisions you can defend in a board meeting.',
    },
];

export function DifferentiatorsSection() {
    return (
        <section id="why-different" className="bg-slate-900/20 py-24 md:py-32 relative">
            {/* Background Mesh */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] pointer-events-none" />

            <Container className="relative z-10">
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
                        The ThreatVeil Difference
                    </p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        What makes us different
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        We built what we wished existed when we were running security at startups.
                    </p>
                </FadeIn>

                <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                    {differentiators.map((item, index) => (
                        <FadeIn key={index} delay={index * 0.1}>
                            <FeatureCard
                                icon={item.icon}
                                title={item.title}
                                description={item.description}
                                accent={item.accent}
                                className="h-full"
                            />
                        </FadeIn>
                    ))}
                </StaggerContainer>
            </Container>
        </section>
    );
}
