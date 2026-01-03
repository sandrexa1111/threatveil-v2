'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, Clock } from 'lucide-react';
import { FadeIn, GlowEffect } from '@/components/ui/motion-primitives';

export function FinalCTASection() {
    return (
        <section className="py-24 md:py-32 bg-slate-950">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                <FadeIn className="relative overflow-hidden rounded-3xl bg-[#0B1120] border border-slate-800 px-8 py-20 sm:px-12 md:py-24 text-center">

                    {/* Background Effects */}
                    <div className="absolute inset-0 z-0">
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[600px] rounded-full bg-cyan-900/20 blur-[100px]" />
                        <div className="absolute inset-0 bg-[url('/noise.svg')] opacity-[0.03] mix-blend-overlay" />
                    </div>

                    <div className="relative z-10 flex flex-col items-center">
                        <h2 className="max-w-2xl text-3xl md:text-5xl font-semibold tracking-tight text-white mb-6 leading-tight">
                            Start making better security decisions today
                        </h2>
                        <p className="max-w-lg text-lg text-slate-400 mb-10 leading-relaxed">
                            Run your first ThreatVeil scan in under 60 seconds. <br />
                            No credit card. No agents. No credentials.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 items-center w-full justify-center">
                            <Link href="/app">
                                <Button size="lg" className="h-14 px-10 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-900 text-lg font-semibold shadow-[0_0_20px_-5px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.6)] transition-all">
                                    Start Free Scan <ArrowRight className="ml-2 h-5 w-5" />
                                </Button>
                            </Link>
                        </div>

                        <p className="mt-8 flex items-center gap-2 text-sm font-medium text-slate-500">
                            <Clock className="h-4 w-4 text-cyan-500/80" />
                            Results in under 60 seconds
                        </p>
                    </div>
                </FadeIn>
            </div>
        </section>
    );
}
