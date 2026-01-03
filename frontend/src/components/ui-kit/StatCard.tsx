'use client';

import { cn } from '@/lib/utils';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { motion } from 'framer-motion';

interface StatCardProps {
    label: string;
    value: string | number;
    icon?: LucideIcon;
    trend?: {
        value: number;
        direction: 'up' | 'down' | 'neutral';
        label?: string;
    };
    variant?: 'default' | 'accent' | 'warning' | 'danger' | 'success';
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const variantStyles = {
    default: {
        icon: 'text-slate-400',
        value: 'text-white',
        border: 'border-slate-800/60',
    },
    accent: {
        icon: 'text-cyan-400',
        value: 'text-white',
        border: 'border-cyan-500/20',
    },
    warning: {
        icon: 'text-amber-400',
        value: 'text-amber-400',
        border: 'border-amber-500/20',
    },
    danger: {
        icon: 'text-red-400',
        value: 'text-red-400',
        border: 'border-red-500/20',
    },
    success: {
        icon: 'text-emerald-400',
        value: 'text-emerald-400',
        border: 'border-emerald-500/20',
    },
};

const sizeStyles = {
    sm: {
        padding: 'p-3',
        iconSize: 'h-4 w-4',
        valueSize: 'text-xl',
        labelSize: 'text-2xs',
        gap: 'gap-1.5',
    },
    md: {
        padding: 'p-4',
        iconSize: 'h-5 w-5',
        valueSize: 'text-2xl',
        labelSize: 'text-xs',
        gap: 'gap-2',
    },
    lg: {
        padding: 'p-5',
        iconSize: 'h-6 w-6',
        valueSize: 'text-3xl',
        labelSize: 'text-sm',
        gap: 'gap-3',
    },
};

/**
 * StatCard - Metric display card with optional trend indicator
 * Used for dashboard KPIs and summary statistics
 */
export function StatCard({
    label,
    value,
    icon: Icon,
    trend,
    variant = 'default',
    size = 'md',
    className,
}: StatCardProps) {
    const styles = variantStyles[variant];
    const sizes = sizeStyles[size];

    const TrendIcon = trend?.direction === 'up'
        ? TrendingUp
        : trend?.direction === 'down'
            ? TrendingDown
            : Minus;

    const trendColor = trend?.direction === 'up'
        ? 'text-emerald-400'
        : trend?.direction === 'down'
            ? 'text-red-400'
            : 'text-slate-500';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
                'rounded-2xl border bg-[#111827]/80 backdrop-blur-sm',
                'hover:bg-[#111827]/90 transition-all duration-200',
                'hover:shadow-card-hover hover:-translate-y-0.5',
                sizes.padding,
                styles.border,
                className
            )}
        >
            <div className={cn('flex flex-col', sizes.gap)}>
                {/* Header: Icon + Label */}
                <div className="flex items-center gap-2">
                    {Icon && (
                        <Icon className={cn(sizes.iconSize, styles.icon)} />
                    )}
                    <span className={cn(
                        'font-medium uppercase tracking-wider text-slate-400',
                        sizes.labelSize
                    )}>
                        {label}
                    </span>
                </div>

                {/* Value + Trend */}
                <div className="flex items-end justify-between">
                    <span className={cn(
                        'font-bold tracking-tight',
                        sizes.valueSize,
                        styles.value
                    )}>
                        {value}
                    </span>

                    {trend && (
                        <div className={cn('flex items-center gap-1', trendColor)}>
                            <TrendIcon className="h-3.5 w-3.5" />
                            <span className="text-xs font-medium">
                                {trend.value > 0 ? '+' : ''}{trend.value}
                                {trend.label && ` ${trend.label}`}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
