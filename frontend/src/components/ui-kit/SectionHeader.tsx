'use client';

import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
    title: string;
    icon?: LucideIcon;
    subtitle?: string;
    description?: string;
    action?: React.ReactNode;
    badge?: React.ReactNode;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const sizeStyles = {
    sm: {
        title: 'text-sm font-medium',
        subtitle: 'text-2xs',
        icon: 'h-3.5 w-3.5',
        gap: 'gap-1.5',
    },
    md: {
        title: 'text-base font-semibold',
        subtitle: 'text-xs',
        icon: 'h-4 w-4',
        gap: 'gap-2',
    },
    lg: {
        title: 'text-lg font-bold',
        subtitle: 'text-sm',
        icon: 'h-5 w-5',
        gap: 'gap-2.5',
    },
};

/**
 * SectionHeader - Consistent header for card sections and panels
 * Includes icon, title, optional subtitle/description, and action slot
 */
export function SectionHeader({
    title,
    icon: Icon,
    subtitle,
    description,
    action,
    badge,
    size = 'md',
    className,
}: SectionHeaderProps) {
    const styles = sizeStyles[size];

    return (
        <div className={cn('flex items-start justify-between', className)}>
            <div className="flex-1 min-w-0">
                <div className={cn('flex items-center', styles.gap)}>
                    {Icon && (
                        <Icon className={cn(styles.icon, 'text-cyan-400 flex-shrink-0')} />
                    )}
                    <h3 className={cn('text-white/95 truncate', styles.title)}>
                        {title}
                    </h3>
                    {badge && <div className="flex-shrink-0">{badge}</div>}
                </div>

                {subtitle && (
                    <p className={cn(
                        'text-slate-500 mt-0.5',
                        styles.subtitle,
                        Icon && 'ml-6' // Align with title when icon present
                    )}>
                        {subtitle}
                    </p>
                )}

                {description && (
                    <p className={cn(
                        'text-slate-400 mt-1.5 text-sm leading-relaxed max-w-2xl',
                        Icon && 'ml-6'
                    )}>
                        {description}
                    </p>
                )}
            </div>

            {action && (
                <div className="flex-shrink-0 ml-4">
                    {action}
                </div>
            )}
        </div>
    );
}
