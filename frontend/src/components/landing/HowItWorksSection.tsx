'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import { Container } from '@/components/layout/Container';
import { Badge } from '@/components/ui/badge';
import { Clock, Zap, Shield, CheckCircle2 } from 'lucide-react';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';
import { cn } from '@/lib/utils';

const steps = [
    {
        num: '01',
        title: 'Enter your domain',
        description: 'Just type your domain—no credentials, no agents, no configuration required.',
        time: '5 sec',
        active: false,
    },
    {
        num: '02',
        title: 'We scan passively',
        description: 'OSINT, DNS, TLS, GitHub repos, CVE databases, AI tool artifacts—all from public sources.',
        time: '45 sec',
        active: true, // Simulate "active" step style for demo
    },
    {
        num: '03',
        title: 'Get 3 priorities',
        description: 'Ranked by exploit likelihood with effort estimates and business-ready explanations.',
        time: '10 sec',
        active: false,
    },
];

const badges = [
    { icon: Shield, text: 'No agents' },
    { icon: Zap, text: 'No credentials' },
    { icon: Clock, text: 'Under 60 seconds' },
];

export function HowItWorksSection() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start center", "end center"]
    });

    const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

    return (
        <section id="how-it-works" className="relative bg-slate-950 py-24 md:py-32" ref={containerRef}>
            <Container>
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">How It Works</p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        From scan to action in under 60 seconds
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        No setup. No waiting. No 1,000-line reports to read.
                    </p>
                </FadeIn>

                {/* Badges */}
                <StaggerContainer className="flex flex-wrap justify-center gap-4 mb-20" delay={0.2} staggerDelay={0.1}>
                    {badges.map((badge, idx) => (
                        <FadeIn key={idx} direction="up" className="inline-block">
                            <Badge
                                variant="outline"
                                className="border-slate-800 bg-slate-900/60 text-slate-300 px-4 py-2 hover:bg-slate-800 transition-colors cursor-default"
                            >
                                <badge.icon className="h-3.5 w-3.5 mr-2 text-emerald-400" />
                                {badge.text}
                            </Badge>
                        </FadeIn>
                    ))}
                </StaggerContainer>

                {/* Timeline */}
                <div className="max-w-3xl mx-auto relative">
                    {/* Main vertical line track */}
                    <div className="absolute left-[27px] top-0 bottom-0 w-[2px] bg-slate-800/50 hidden md:block" />

                    {/* Animated Fill Line */}
                    <motion.div
                        className="absolute left-[27px] top-0 w-[2px] bg-gradient-to-b from-cyan-500 via-purple-500 to-cyan-500 hidden md:block"
                        style={{ height: lineHeight }}
                    />

                    <div className="space-y-12">
                        {steps.map((step, index) => (
                            <FadeIn
                                key={index}
                                delay={index * 0.2}
                                className={cn(
                                    "relative flex items-start gap-8 group",
                                    step.active ? "opacity-100" : "opacity-70 hover:opacity-100 transition-opacity duration-500"
                                )}
                            >
                                {/* Step Number / Indicator */}
                                <div className="relative z-10 flex-shrink-0 h-14 w-14 rounded-full bg-[#0B1120] border-2 border-slate-800 flex items-center justify-center font-mono text-sm font-bold text-slate-500 transition-all duration-500 group-hover:border-cyan-500/50 group-hover:text-cyan-400 group-hover:scale-110 shadow-lg">
                                    {step.num}
                                    {step.active && (
                                        <div className="absolute inset-0 rounded-full border-2 border-cyan-500/80 animate-pulse-slow" />
                                    )}
                                </div>

                                <div className="pt-2 flex-1">
                                    <div className="flex items-center gap-4 mb-2">
                                        <h3 className={cn(
                                            "text-xl font-semibold transition-colors duration-300",
                                            step.active ? "text-white" : "text-slate-300 group-hover:text-white"
                                        )}>
                                            {step.title}
                                        </h3>
                                        <span className="text-xs font-mono text-cyan-400/80 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded">
                                            ~{step.time}
                                        </span>
                                    </div>
                                    <p className="text-base text-slate-400 leading-relaxed max-w-xl">
                                        {step.description}
                                    </p>
                                </div>
                            </FadeIn>
                        ))}
                    </div>
                </div>
            </Container>
        </section>
    );
}
