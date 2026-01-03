'use client';

import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
    variant?: 'text' | 'card' | 'stat' | 'row' | 'circle' | 'badge';
    className?: string;
    count?: number;
}

/**
 * LoadingSkeleton - Shimmer loading states for various UI elements
 * Provides consistent loading experience across the application
 */
export function LoadingSkeleton({
    variant = 'text',
    className,
    count = 1,
}: LoadingSkeletonProps) {
    const items = Array.from({ length: count }, (_, i) => i);

    const baseClasses = cn(
        'animate-pulse rounded bg-gradient-to-r from-slate-800/60 via-slate-700/40 to-slate-800/60',
        'bg-[length:200%_100%] animate-shimmer'
    );

    const renderSkeleton = (key: number) => {
        switch (variant) {
            case 'text':
                return (
                    <div key={key} className={cn(baseClasses, 'h-4 w-full', className)} />
                );

            case 'card':
                return (
                    <div
                        key={key}
                        className={cn(
                            'rounded-2xl border border-slate-800/60 bg-[#111827]/80 p-4 space-y-4',
                            className
                        )}
                    >
                        <div className={cn(baseClasses, 'h-4 w-1/3')} />
                        <div className={cn(baseClasses, 'h-12 w-full')} />
                        <div className="space-y-2">
                            <div className={cn(baseClasses, 'h-3 w-full')} />
                            <div className={cn(baseClasses, 'h-3 w-4/5')} />
                        </div>
                    </div>
                );

            case 'stat':
                return (
                    <div
                        key={key}
                        className={cn(
                            'rounded-2xl border border-slate-800/60 bg-[#111827]/80 p-4 space-y-3',
                            className
                        )}
                    >
                        <div className="flex items-center gap-2">
                            <div className={cn(baseClasses, 'h-4 w-4 rounded')} />
                            <div className={cn(baseClasses, 'h-3 w-16')} />
                        </div>
                        <div className={cn(baseClasses, 'h-8 w-20')} />
                    </div>
                );

            case 'row':
                return (
                    <div
                        key={key}
                        className={cn(
                            'flex items-center gap-4 py-3 px-4 border-b border-slate-800/30',
                            className
                        )}
                    >
                        <div className={cn(baseClasses, 'h-8 w-8 rounded-md flex-shrink-0')} />
                        <div className="flex-1 space-y-2">
                            <div className={cn(baseClasses, 'h-4 w-1/3')} />
                            <div className={cn(baseClasses, 'h-3 w-1/2')} />
                        </div>
                        <div className={cn(baseClasses, 'h-6 w-16 rounded-full')} />
                    </div>
                );

            case 'circle':
                return (
                    <div
                        key={key}
                        className={cn(baseClasses, 'h-10 w-10 rounded-full', className)}
                    />
                );

            case 'badge':
                return (
                    <div
                        key={key}
                        className={cn(baseClasses, 'h-5 w-16 rounded-full', className)}
                    />
                );

            default:
                return (
                    <div key={key} className={cn(baseClasses, 'h-4 w-full', className)} />
                );
        }
    };

    return (
        <>
            {items.map(renderSkeleton)}
        </>
    );
}

/**
 * SkeletonCard - Loading skeleton for full card containers
 */
export function SkeletonCard({ className }: { className?: string }) {
    return (
        <div
            className={cn(
                'rounded-2xl border border-slate-800/60 bg-[#111827]/80 p-6 space-y-6',
                className
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <LoadingSkeleton variant="circle" className="h-5 w-5" />
                    <LoadingSkeleton variant="text" className="h-4 w-32" />
                </div>
                <LoadingSkeleton variant="badge" className="w-20" />
            </div>

            {/* Content */}
            <div className="space-y-4">
                <LoadingSkeleton variant="row" />
                <LoadingSkeleton variant="row" />
                <LoadingSkeleton variant="row" />
            </div>
        </div>
    );
}

/**
 * SkeletonTable - Loading skeleton for tables
 */
export function SkeletonTable({
    rows = 5,
    columns = 4,
    className
}: {
    rows?: number;
    columns?: number;
    className?: string;
}) {
    return (
        <div className={cn('rounded-xl border border-slate-800/60 overflow-hidden', className)}>
            {/* Header */}
            <div className="bg-slate-900/50 border-b border-slate-800/50 px-4 py-3">
                <div className="flex gap-4">
                    {Array.from({ length: columns }).map((_, i) => (
                        <LoadingSkeleton
                            key={i}
                            variant="text"
                            className={cn('h-3', i === 0 ? 'w-1/4' : 'w-16')}
                        />
                    ))}
                </div>
            </div>

            {/* Rows */}
            {Array.from({ length: rows }).map((_, i) => (
                <div
                    key={i}
                    className="border-b border-slate-800/30 px-4 py-4 last:border-b-0"
                >
                    <div className="flex items-center gap-4">
                        {Array.from({ length: columns }).map((_, j) => (
                            <LoadingSkeleton
                                key={j}
                                variant="text"
                                className={cn('h-4', j === 0 ? 'w-1/4' : 'w-20')}
                            />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

/**
 * SkeletonStats - Loading skeleton for stat card grid
 */
export function SkeletonStats({
    count = 4,
    className
}: {
    count?: number;
    className?: string;
}) {
    return (
        <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-4', className)}>
            {Array.from({ length: count }).map((_, i) => (
                <LoadingSkeleton key={i} variant="stat" />
            ))}
        </div>
    );
}
