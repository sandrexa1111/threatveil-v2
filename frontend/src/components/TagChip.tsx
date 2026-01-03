'use client';

import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface TagChipProps {
    label: string;
    icon?: LucideIcon;
    isActive?: boolean;
    showDot?: boolean;
    variant?: 'default' | 'outline' | 'muted';
    className?: string;
}

/**
 * TagChip - Consistent chip/badge styling
 * Used for data sources, status badges, filters
 * 
 * @param isActive - Shows green dot when true, gray when false
 * @param showDot - Whether to show the status indicator dot
 */
export function TagChip({
    label,
    icon: Icon,
    isActive = true,
    showDot = false,
    variant = 'default',
    className
}: TagChipProps) {
    const baseStyles = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-default";

    const variants = {
        default: "bg-gray-800/50 border border-gray-700/50 text-gray-300 hover:bg-gray-800 hover:border-gray-600",
        outline: "bg-transparent border border-gray-700 text-gray-400 hover:bg-gray-800/30",
        muted: "bg-gray-900/50 text-gray-500 hover:text-gray-400",
    };

    return (
        <div className={cn(baseStyles, variants[variant], className)}>
            {showDot && (
                <span className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    isActive ? "bg-emerald-500" : "bg-gray-600"
                )} />
            )}
            {Icon && <Icon className="h-3 w-3 text-gray-400" />}
            <span>{label}</span>
        </div>
    );
}

/**
 * StatusBadge - For risk levels and status indicators
 */
interface StatusBadgeProps {
    level: 'low' | 'medium' | 'high' | 'critical';
    label?: string;
    className?: string;
}

export function StatusBadge({ level, label, className }: StatusBadgeProps) {
    const levelStyles = {
        low: "bg-green-500/10 text-green-400 border-green-500/20",
        medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
        high: "bg-red-500/10 text-red-400 border-red-500/20",
        critical: "bg-red-600/20 text-red-300 border-red-500/30",
    };

    const defaultLabels = {
        low: 'Low Risk',
        medium: 'Medium Risk',
        high: 'High Risk',
        critical: 'Critical',
    };

    return (
        <span className={cn(
            "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
            levelStyles[level],
            className
        )}>
            {label || defaultLabels[level]}
        </span>
    );
}

/**
 * Helper to get risk level from score
 */
export function getRiskLevel(score: number): 'low' | 'medium' | 'high' {
    if (score >= 70) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
}
