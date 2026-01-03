'use client';

import { Container } from '@/components/layout/Container';
import { AudienceCard } from './LandingCards';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const audiences = [
    {
        emoji: '🚀',
        title: 'SaaS Startups',
        problem: 'No dedicated security team, but SOC 2 audits are coming.',
        solution: 'Get weekly security priorities without hiring a CISO.',
    },
    {
        emoji: '🧠',
        title: 'AI-Driven Companies',
        problem: 'Exposed API keys, shadow AI tools, and audit blindspots.',
        solution: 'First-class visibility into AI-specific security risks.',
    },
    {
        emoji: '🛠️',
        title: 'DevOps & Platform Teams',
        problem: 'Security is an afterthought—too many tools, too little time.',
        solution: 'One dashboard, 3 priorities, zero alert fatigue.',
    },
    {
        emoji: '🧩',
        title: 'Security Owners',
        problem: 'You\'re the "security person" but have 10 other jobs.',
        solution: 'Decision-ready outputs you can share with executives.',
    },
];

export function AudienceSection() {
    return (
        <section id="who-its-for" className="bg-slate-900/30 py-24 md:py-32 border-y border-slate-800/30">
            <Container>
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
                        Who It&apos;s For
                    </p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        Built for teams without a Security Operations Center
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        If you don&apos;t have 24/7 analysts watching dashboards, we&apos;re built for you.
                    </p>
                </FadeIn>

                <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
                    {audiences.map((audience, index) => (
                        <FadeIn key={index}>
                            <AudienceCard {...audience} />
                        </FadeIn>
                    ))}
                </StaggerContainer>
            </Container>
        </section>
    );
}
