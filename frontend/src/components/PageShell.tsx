'use client';

import { cn } from '@/lib/utils';

interface PageShellProps {
    children: React.ReactNode;
    className?: string;
}

/**
 * PageShell - Consistent page wrapper with gradient background
 * Used on all main content pages for unified styling
 */
export function PageShell({ children, className }: PageShellProps) {
    return (
        <div className={cn(
            "min-h-screen bg-gradient-to-b from-[#0B0F19] to-[#111827]",
            className
        )}>
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </div>
        </div>
    );
}
