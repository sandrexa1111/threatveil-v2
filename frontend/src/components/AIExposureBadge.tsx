'use client';

import { cn } from '@/lib/utils';
import { ShieldCheck, ShieldAlert, ShieldX, Brain } from 'lucide-react';

interface AIExposureBadgeProps {
    score: number;
    size?: 'sm' | 'md' | 'lg';
    showIcon?: boolean;
    showLabel?: boolean;
}

/**
 * AIExposureBadge - Displays AI exposure level based on score
 * 
 * Thresholds:
 * - score <= 20: "AI-Safe" (green)
 * - score <= 50: "AI-Moderate Risk" (amber)
 * - score > 50: "AI-High Exposure" (red)
 */
export function AIExposureBadge({
    score,
    size = 'md',
    showIcon = true,
    showLabel = true
}: AIExposureBadgeProps) {
    const getExposureInfo = (score: number) => {
        if (score <= 20) {
            return {
                level: 'AI-Safe',
                shortLevel: 'Safe',
                color: 'text-emerald-400',
                bgColor: 'bg-emerald-500/10',
                borderColor: 'border-emerald-500/30',
                icon: ShieldCheck,
            };
        }
        if (score <= 50) {
            return {
                level: 'AI-Moderate Risk',
                shortLevel: 'Moderate',
                color: 'text-amber-400',
                bgColor: 'bg-amber-500/10',
                borderColor: 'border-amber-500/30',
                icon: ShieldAlert,
            };
        }
        return {
            level: 'AI-High Exposure',
            shortLevel: 'High Risk',
            color: 'text-red-400',
            bgColor: 'bg-red-500/10',
            borderColor: 'border-red-500/30',
            icon: ShieldX,
        };
    };

    const exposure = getExposureInfo(score);
    const Icon = showIcon ? exposure.icon : null;

    const sizeClasses = {
        sm: 'px-2 py-0.5 text-xs gap-1',
        md: 'px-2.5 py-1 text-xs gap-1.5',
        lg: 'px-3 py-1.5 text-sm gap-2',
    };

    const iconSizes = {
        sm: 'h-3 w-3',
        md: 'h-3.5 w-3.5',
        lg: 'h-4 w-4',
    };

    return (
        <span
            className={cn(
                'inline-flex items-center rounded-full border font-medium transition-colors',
                sizeClasses[size],
                exposure.bgColor,
                exposure.borderColor,
                exposure.color
            )}
        >
            {Icon && <Icon className={iconSizes[size]} />}
            {showLabel && (
                <span>{size === 'sm' ? exposure.shortLevel : exposure.level}</span>
            )}
        </span>
    );
}

/**
 * AIExposureBadgeFromLevel - Alternative that takes level string directly
 */
export function AIExposureBadgeFromLevel({
    level,
    size = 'md'
}: {
    level: 'low' | 'moderate' | 'high';
    size?: 'sm' | 'md' | 'lg';
}) {
    const scoreMap = {
        low: 10,
        moderate: 35,
        high: 75,
    };
    return <AIExposureBadge score={scoreMap[level]} size={size} />;
}
