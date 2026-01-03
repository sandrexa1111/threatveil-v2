'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import {
    AlertTriangle,
    Shield,
    CheckCircle,
    Clock,
    Play,
    Brain,
    ShieldAlert,
    Zap
} from 'lucide-react';

const riskBadgeVariants = cva(
    'inline-flex items-center gap-1 rounded-full text-xs font-medium border transition-colors',
    {
        variants: {
            variant: {
                // Severity variants
                high: 'bg-red-500/10 text-red-400 border-red-500/20',
                medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                critical: 'bg-red-600/15 text-red-300 border-red-500/30',

                // AI exposure variants
                'ai-high': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
                'ai-medium': 'bg-purple-500/10 text-purple-300 border-purple-500/15',
                'ai-low': 'bg-slate-500/10 text-slate-400 border-slate-500/20',

                // Status variants
                pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                'in-progress': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
                resolved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',

                // Source/neutral variants
                source: 'bg-slate-800/60 text-slate-300 border-slate-700/50',
                accent: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
                neutral: 'bg-slate-800/50 text-slate-400 border-slate-700/40',
            },
            size: {
                xs: 'px-1.5 py-0.5 text-2xs',
                sm: 'px-2 py-0.5 text-xs',
                md: 'px-2.5 py-1 text-xs',
                lg: 'px-3 py-1.5 text-sm',
            },
        },
        defaultVariants: {
            variant: 'neutral',
            size: 'sm',
        },
    }
);

// Icon mapping for variants
const variantIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    high: AlertTriangle,
    critical: AlertTriangle,
    medium: ShieldAlert,
    low: Shield,
    'ai-high': Brain,
    'ai-medium': Brain,
    'ai-low': Brain,
    pending: Clock,
    'in-progress': Play,
    resolved: CheckCircle,
    accent: Zap,
};

interface RiskBadgeProps extends VariantProps<typeof riskBadgeVariants> {
    children: React.ReactNode;
    showIcon?: boolean;
    className?: string;
}

/**
 * RiskBadge - Unified badge component for risk, AI, status, and source indicators
 * Replaces multiple badge variants with a single consistent component
 */
export function RiskBadge({
    children,
    variant,
    size,
    showIcon = false,
    className,
}: RiskBadgeProps) {
    const Icon = variant ? variantIcons[variant] : null;

    return (
        <span className={cn(riskBadgeVariants({ variant, size }), className)}>
            {showIcon && Icon && (
                <Icon className={cn(
                    size === 'xs' || size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'
                )} />
            )}
            {children}
        </span>
    );
}

// Convenience exports for common badge types
export function SeverityBadge({
    severity,
    size = 'sm',
    showIcon = true,
}: {
    severity: 'high' | 'medium' | 'low' | 'critical';
    size?: 'xs' | 'sm' | 'md' | 'lg';
    showIcon?: boolean;
}) {
    const labels = {
        critical: 'Critical',
        high: 'High',
        medium: 'Medium',
        low: 'Low',
    };

    return (
        <RiskBadge variant={severity} size={size} showIcon={showIcon}>
            {labels[severity]}
        </RiskBadge>
    );
}

export function AIExposureBadge({
    level,
    size = 'sm',
    showIcon = true,
}: {
    level: 'high' | 'medium' | 'low';
    size?: 'xs' | 'sm' | 'md' | 'lg';
    showIcon?: boolean;
}) {
    const labels = {
        high: 'High AI Exposure',
        medium: 'Moderate AI',
        low: 'Low AI',
    };

    return (
        <RiskBadge variant={`ai-${level}` as const} size={size} showIcon={showIcon}>
            {labels[level]}
        </RiskBadge>
    );
}

export function StatusBadge({
    status,
    size = 'sm',
    showIcon = true,
}: {
    status: 'pending' | 'in-progress' | 'resolved';
    size?: 'xs' | 'sm' | 'md' | 'lg';
    showIcon?: boolean;
}) {
    const labels = {
        pending: 'Pending',
        'in-progress': 'In Progress',
        resolved: 'Resolved',
    };

    return (
        <RiskBadge variant={status} size={size} showIcon={showIcon}>
            {labels[status]}
        </RiskBadge>
    );
}

export function SourceBadge({
    source,
    size = 'sm',
}: {
    source: string;
    size?: 'xs' | 'sm' | 'md' | 'lg';
}) {
    return (
        <RiskBadge variant="source" size={size}>
            {source}
        </RiskBadge>
    );
}
