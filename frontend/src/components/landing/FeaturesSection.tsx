'use client';

import { motion } from 'framer-motion';
import { Eye, Key, FileText, Shield } from 'lucide-react';
import { Container } from '@/components/layout/Container';

const features = [
    {
        icon: Eye,
        title: 'Passive OSINT Scanning',
        description: 'We never touch your infrastructure. All scans are 100% passive and safe for production.',
        trust: 'No agents. No credentials required.',
    },
    {
        icon: Key,
        title: 'AI Footprint Detection',
        description: 'Identify exposed API keys, model endpoints, and AI tool misconfigurations before attackers do.',
        trust: 'Covers OpenAI, Anthropic, HuggingFace, and more.',
    },
    {
        icon: FileText,
        title: 'Plain-English Actions',
        description: 'Stop deciphering CVE numbers. We translate findings into prioritized, fix-ready recommendations.',
        trust: 'No security expertise required.',
    },
    {
        icon: Shield,
        title: 'Deterministic Scoring',
        description: 'No AI hallucinations. Your risk score is calculated with transparent, auditable logic.',
        trust: 'Every score is explainable.',
    },
];

export function FeaturesSection() {
    return (
        <section id="features" className="bg-slate-950 py-20 md:py-24">
            <Container>
                <div className="mx-auto mb-12 max-w-xl text-center">
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">How It Works</p>
                    <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-white">
                        From signal noise to security clarity
                    </h2>
                    <p className="mt-4 text-base text-slate-400">
                        Built for teams without a SOC. Designed for the AI era.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.4, delay: index * 0.1 }}
                            className="h-full"
                        >
                            <div className="h-full rounded-xl border border-slate-800/60 bg-slate-900/40 p-5 hover:bg-slate-900/60 transition-colors flex flex-col">
                                <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800/80 text-cyan-400">
                                    <feature.icon className="h-5 w-5" />
                                </div>
                                <h3 className="text-base font-semibold text-white mb-2">
                                    {feature.title}
                                </h3>
                                <p className="text-sm text-slate-400 leading-relaxed mb-3 flex-1">
                                    {feature.description}
                                </p>
                                <p className="text-xs text-slate-500">
                                    {feature.trust}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </Container>
        </section>
    );
}
