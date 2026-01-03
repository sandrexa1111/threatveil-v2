'use client';

import { cn } from '@/lib/utils';
import { LucideIcon, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { GlowEffect } from '@/components/ui/motion-primitives';

// --- Types ---

interface FeatureCardProps {
    icon: any; // Using any for now to accept both Lucide and Custom motion icons
    title: string;
    description: string;
    details?: string[];
    accent?: boolean;
    className?: string;
}

interface AudienceCardProps {
    emoji: string;
    title: string;
    problem: string;
    solution: string;
    className?: string;
}

interface PricingCardProps {
    name: string;
    price: string;
    period?: string;
    description: string;
    features: string[];
    cta: string;
    highlighted?: boolean;
    badge?: string;
    className?: string;
}

interface TrustBadgeProps {
    icon: any;
    text: string;
    className?: string;
}

// --- Components ---

export function FeatureCard({
    icon: Icon,
    title,
    description,
    details,
    accent = false,
    className
}: FeatureCardProps) {
    return (
        <motion.div
            className={cn(
                'group relative h-full rounded-xl border p-6 transition-all duration-500 overflow-hidden',
                accent
                    ? 'border-cyan-500/30 bg-cyan-950/10'
                    : 'border-slate-800/60 bg-slate-900/40 hover:bg-slate-900/60 hover:border-slate-700',
                className
            )}
            whileHover={{ y: -4 }}
        >
            <GlowEffect />

            <div className={cn(
                'mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg transition-colors duration-300',
                accent ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-800/50 text-slate-400 group-hover:text-cyan-400 group-hover:bg-slate-800'
            )}>
                <Icon className="h-6 w-6" />
            </div>

            <h3 className="text-lg font-semibold text-white mb-3 group-hover:text-cyan-50 transition-colors">{title}</h3>
            <p className="text-sm text-slate-400 leading-relaxed mb-4 group-hover:text-slate-300 transition-colors">{description}</p>

            {details && details.length > 0 && (
                <ul className="space-y-2 border-t border-slate-800/50 pt-4 mt-auto">
                    {details.map((detail, idx) => (
                        <li key={idx} className="text-xs text-slate-500 flex items-center gap-2 group-hover:text-slate-400 transition-colors">
                            <span className="h-1 w-1 rounded-full bg-cyan-500/50" />
                            {detail}
                        </li>
                    ))}
                </ul>
            )}
        </motion.div>
    );
}

export function AudienceCard({
    emoji,
    title,
    problem,
    solution,
    className
}: AudienceCardProps) {
    return (
        <motion.div
            className={cn(
                'group relative rounded-2xl border border-slate-800/60 bg-[#0B1120]/80 p-6 md:p-8 hover:bg-[#0F172A] transition-all duration-300 overflow-hidden',
                className
            )}
            whileHover={{ scale: 1.01 }}
        >
            {/* Hover Glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            <div className="flex items-start gap-5 relative z-10">
                <span className="text-4xl filter grayscale group-hover:grayscale-0 transition-all duration-500 transform group-hover:scale-110 block">{emoji}</span>
                <div className="flex-1">
                    <h3 className="text-lg font-bold text-white mb-3 tracking-tight">{title}</h3>

                    <div className="space-y-3">
                        <div className="flex gap-3 text-sm">
                            <span className="text-red-400/80 font-medium whitespace-nowrap">Problem:</span>
                            <span className="text-slate-400 leading-relaxed">{problem}</span>
                        </div>
                        <div className="flex gap-3 text-sm">
                            <span className="text-cyan-400 font-medium whitespace-nowrap">Solution:</span>
                            <span className="text-slate-200 leading-relaxed">{solution}</span>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

export function PricingCard({
    name,
    price,
    period = '/month',
    description,
    features,
    cta,
    highlighted = false,
    badge,
    className
}: PricingCardProps) {
    return (
        <motion.div
            className={cn(
                'relative flex flex-col rounded-2xl border p-8 transition-all duration-500',
                highlighted
                    ? 'border-cyan-500/50 bg-[#0B1120] shadow-[0_0_40px_-10px_rgba(34,211,238,0.15)]'
                    : 'border-slate-800 bg-slate-900/20 hover:border-slate-700',
                className
            )}
            whileHover={highlighted ? { scale: 1.02 } : { y: -5 }}
        >
            {badge && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="inline-block rounded-full bg-cyan-500 px-4 py-1 text-xs font-bold uppercase tracking-wider text-slate-900 shadow-lg shadow-cyan-500/20">
                        {badge}
                    </span>
                </div>
            )}

            <div className="text-center mb-8">
                <h3 className={cn("text-lg font-semibold mb-2", highlighted ? "text-cyan-400" : "text-white")}>{name}</h3>
                <p className="text-sm text-slate-400 mb-6 min-h-[40px]">{description}</p>
                <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold text-white tracking-tight">{price}</span>
                    {period && price !== 'Custom' && price !== 'Free' && (
                        <span className="text-sm text-slate-500 font-medium">{period}</span>
                    )}
                </div>
            </div>

            <ul className="space-y-4 mb-8 flex-1">
                {features.map((feature, idx) => (
                    <motion.li
                        key={idx}
                        className="flex items-start gap-3 text-sm text-slate-300"
                        initial={{ opacity: 0, x: -10 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <CheckCircle2 className={cn("h-5 w-5 flex-shrink-0", highlighted ? "text-cyan-400" : "text-slate-600")} />
                        <span className="leading-snug">{feature}</span>
                    </motion.li>
                ))}
            </ul>

            <button className={cn(
                'w-full rounded-xl py-3.5 text-sm font-semibold transition-all duration-300',
                highlighted
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-900 shadow-[0_0_20px_-5px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.6)]'
                    : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 hover:border-slate-600'
            )}>
                {cta}
            </button>
        </motion.div>
    );
}

export function TrustBadge({ icon: Icon, text, className }: TrustBadgeProps) {
    return (
        <motion.div
            className={cn(
                'flex items-center gap-3 rounded-full bg-slate-900/40 border border-slate-800/60 px-5 py-3 backdrop-blur-sm hover:bg-slate-800/40 hover:border-slate-700/80 transition-all cursor-default',
                className
            )}
            whileHover={{ scale: 1.05 }}
        >
            <Icon className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-medium text-slate-300">{text}</span>
        </motion.div>
    );
}
