'use client';

import { IconTarget, IconLock, IconScan, IconShield } from '@/components/ui/custom-icons';
import { Container } from '@/components/layout/Container';
import { TrustBadge } from './LandingCards';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const trustItems = [
    {
        icon: IconScan,
        text: 'Passive-only scanning',
    },
    {
        icon: IconLock,
        text: 'No credentials stored',
    },
    {
        icon: IconShield,
        text: 'No agents installed',
    },
    {
        icon: IconTarget,
        text: 'Explainable AI decisions',
    },
];

export function TrustSection() {
    return (
        <section id="trust" className="bg-slate-900/50 py-20 border-t border-slate-800/30">
            <Container>
                <div className="mx-auto max-w-3xl">
                    <FadeIn className="text-center mb-10">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
                            Security & Privacy
                        </p>
                        <h2 className="text-2xl font-semibold text-white mb-3">
                            Safe by design
                        </h2>
                        <p className="text-sm text-slate-400">
                            We never touch your infrastructure. Everything we do is passive and read-only.
                        </p>
                    </FadeIn>

                    <StaggerContainer
                        className="flex flex-wrap justify-center gap-4"
                        staggerDelay={0.1}
                    >
                        {trustItems.map((item, index) => (
                            <FadeIn key={index}>
                                <TrustBadge icon={item.icon} text={item.text} />
                            </FadeIn>
                        ))}
                    </StaggerContainer>
                </div>
            </Container>
        </section>
    );
}
