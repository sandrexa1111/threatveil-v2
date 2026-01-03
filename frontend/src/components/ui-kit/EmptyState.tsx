'use client';

import { cn } from '@/lib/utils';
import { LucideIcon, ShieldOff, FileSearch, Inbox, Database, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

interface EmptyStateProps {
    title: string;
    description?: string;
    icon?: LucideIcon | 'shield' | 'file' | 'inbox' | 'database' | 'search';
    action?: {
        label: string;
        href?: string;
        onClick?: () => void;
    };
    variant?: 'default' | 'compact';
    className?: string;
}

const iconMap: Record<string, LucideIcon> = {
    shield: ShieldOff,
    file: FileSearch,
    inbox: Inbox,
    database: Database,
    search: Search,
};

/**
 * EmptyState - Premium empty state component for lists and panels
 * Features abstract geometric background pattern (no external images)
 */
export function EmptyState({
    title,
    description,
    icon = 'inbox',
    action,
    variant = 'default',
    className,
}: EmptyStateProps) {
    const Icon = typeof icon === 'string' ? iconMap[icon] : icon;
    const isCompact = variant === 'compact';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={cn(
                'flex flex-col items-center justify-center text-center relative overflow-hidden',
                isCompact ? 'py-8 px-4' : 'py-16 px-6',
                className
            )}
        >
            {/* Abstract geometric background pattern */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03]">
                <svg className="w-full h-full" viewBox="0 0 400 300" fill="none">
                    {/* Hexagon grid pattern */}
                    <pattern id="hex-pattern" x="0" y="0" width="60" height="52" patternUnits="userSpaceOnUse">
                        <path
                            d="M30 0L60 15V45L30 60L0 45V15L30 0Z"
                            stroke="currentColor"
                            strokeWidth="1"
                            fill="none"
                        />
                    </pattern>
                    <rect width="100%" height="100%" fill="url(#hex-pattern)" />

                    {/* Decorative circles */}
                    <circle cx="320" cy="80" r="40" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.5" />
                    <circle cx="320" cy="80" r="60" stroke="currentColor" strokeWidth="0.3" fill="none" opacity="0.3" />
                    <circle cx="80" cy="220" r="30" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.4" />
                </svg>
            </div>

            {/* Icon container with gradient ring */}
            <div className={cn(
                'relative mb-4',
                isCompact ? 'mb-3' : 'mb-5'
            )}>
                {/* Outer glow ring */}
                <div className={cn(
                    'absolute inset-0 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-xl',
                    isCompact ? 'scale-75' : ''
                )} />

                {/* Icon background */}
                <div className={cn(
                    'relative rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center',
                    isCompact ? 'h-14 w-14' : 'h-20 w-20'
                )}>
                    {Icon && (
                        <Icon className={cn(
                            'text-slate-500',
                            isCompact ? 'h-6 w-6' : 'h-9 w-9'
                        )} />
                    )}
                </div>
            </div>

            {/* Title */}
            <h3 className={cn(
                'font-semibold text-white/90 mb-2',
                isCompact ? 'text-base' : 'text-lg'
            )}>
                {title}
            </h3>

            {/* Description */}
            {description && (
                <p className={cn(
                    'text-slate-400 max-w-sm leading-relaxed',
                    isCompact ? 'text-xs mb-4' : 'text-sm mb-6'
                )}>
                    {description}
                </p>
            )}

            {/* Action button */}
            {action && (
                <Button
                    onClick={action.onClick}
                    className={cn(
                        'bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium',
                        isCompact ? 'h-8 text-xs' : ''
                    )}
                    asChild={!!action.href}
                >
                    {action.href ? (
                        <a href={action.href}>{action.label}</a>
                    ) : (
                        action.label
                    )}
                </Button>
            )}
        </motion.div>
    );
}
