'use client';

import { cn } from '@/lib/utils';
import { SectionHeader } from '@/components/ui-kit';
import { LucideIcon } from 'lucide-react';

interface SectionCardProps {
    title?: string;
    icon?: LucideIcon;
    subtitle?: string;
    headerAction?: React.ReactNode;
    children: React.ReactNode;
    className?: string;
    contentClassName?: string;
    noPadding?: boolean;
}

/**
 * SectionCard - Reusable card with consistent styling
 * Matches the premium SaaS design system
 */
export function SectionCard({
    title,
    icon,
    subtitle,
    headerAction,
    children,
    className,
    contentClassName,
    noPadding = false,
}: SectionCardProps) {
    return (
        <div className={cn(
            'rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm',
            'hover:border-slate-700/60 transition-colors',
            className
        )}>
            {(title || headerAction) && (
                <div className="px-6 py-4 border-b border-slate-800/50">
                    <SectionHeader
                        title={title || ''}
                        icon={icon}
                        subtitle={subtitle}
                        action={headerAction}
                    />
                </div>
            )}
            <div className={cn(
                noPadding ? '' : 'p-6',
                contentClassName
            )}>
                {children}
            </div>
        </div>
    );
}
