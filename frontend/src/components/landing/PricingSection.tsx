'use client';

import { Container } from '@/components/layout/Container';
import { PricingCard } from './LandingCards';
import { FadeIn, StaggerContainer } from '@/components/ui/motion-primitives';

const tiers = [
    {
        name: 'Free',
        price: 'Free',
        period: '',
        description: 'Try ThreatVeil on a single domain',
        features: [
            '1 domain scan',
            'Full risk assessment',
            '3 prioritized actions',
            'AI-powered explanations',
            'PDF export',
        ],
        cta: 'Start Free Scan',
        highlighted: false,
    },
    {
        name: 'Pro',
        price: '$99',
        period: '/month',
        description: 'Continuous monitoring for growing teams',
        features: [
            'Unlimited domains',
            'Weekly automated scans',
            'GitHub organization scanning',
            'AI exposure monitoring',
            'Email weekly briefs',
            'Slack integration',
            'Priority support',
        ],
        cta: 'Start 14-Day Trial',
        highlighted: true,
        badge: 'Most Popular',
    },
    {
        name: 'Business',
        price: 'Custom',
        period: '',
        description: 'Enterprise features for larger teams',
        features: [
            'Everything in Pro',
            'SSO / SAML authentication',
            'Custom integrations',
            'Dedicated success manager',
            'SOC 2 compliance report',
            'SLA guarantee',
            'On-call security reviews',
        ],
        cta: 'Contact Sales',
        highlighted: false,
    },
];

export function PricingSection() {
    return (
        <section id="pricing" className="bg-slate-950 py-24 md:py-32 relative overflow-hidden">
            {/* Glow effect behind Pricing */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-cyan-900/10 rounded-full blur-[120px] pointer-events-none" />

            <Container className="relative z-10">
                <FadeIn className="mx-auto mb-16 max-w-xl text-center">
                    <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
                        Simple Pricing
                    </p>
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
                        Start free. Scale as you grow.
                    </h2>
                    <p className="text-lg text-slate-400 leading-relaxed">
                        No credit card required. No sales calls for small teams.
                    </p>
                </FadeIn>

                <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    {tiers.map((tier, index) => (
                        <FadeIn key={index} delay={index * 0.15}>
                            <PricingCard {...tier} className="h-full" />
                        </FadeIn>
                    ))}
                </StaggerContainer>
            </Container>
        </section>
    );
}
