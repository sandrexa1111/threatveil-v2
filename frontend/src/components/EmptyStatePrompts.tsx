'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
    Plus,
    Activity,
    Shield,
    Server,
    Bot,
    ArrowRight
} from 'lucide-react';
import Link from 'next/link';

interface EmptyStatePromptsProps {
    type: 'overview' | 'ai-security' | 'assets' | 'scans' | 'asset-detail';
    orgId?: string;
    className?: string;
}

const emptyStateConfig = {
    'overview': {
        icon: Shield,
        title: 'Start monitoring your attack surface',
        description: 'Add your first asset to begin. We\'ll scan for security risks and provide weekly priorities.',
        primaryAction: {
            label: 'Add Asset',
            href: '/app/assets',
            icon: Plus,
        },
        secondaryAction: {
            label: 'Run a Scan',
            href: '/app/scans',
            icon: Activity,
        },
    },
    'ai-security': {
        icon: Bot,
        title: 'No AI exposure detected',
        description: 'We haven\'t found any exposed AI tools, frameworks, or API keys in your monitored assets.',
        primaryAction: {
            label: 'View Scans',
            href: '/app/scans',
            icon: Activity,
        },
        secondaryAction: undefined,
    },
    'assets': {
        icon: Server,
        title: 'No assets yet',
        description: 'Add domains, GitHub organizations, or cloud accounts to start monitoring.',
        primaryAction: {
            label: 'Add Asset',
            href: '/app/assets',
            icon: Plus,
        },
        secondaryAction: undefined,
    },
    'scans': {
        icon: Activity,
        title: 'No scans yet',
        description: 'Run your first scan to discover vulnerabilities and get prioritized recommendations.',
        primaryAction: {
            label: 'Start Scan',
            href: '/app/scans',
            icon: Activity,
        },
        secondaryAction: undefined,
    },
    'asset-detail': {
        icon: Activity,
        title: 'No scan history',
        description: 'This asset hasn\'t been scanned yet. Run a scan to see risk history.',
        primaryAction: {
            label: 'Scan Now',
            href: '/app/scans',
            icon: Activity,
        },
        secondaryAction: undefined,
    },
};

export function EmptyStatePrompts({ type, className }: EmptyStatePromptsProps) {
    const config = emptyStateConfig[type];
    const Icon = config.icon;

    return (
        <Card className={cn('border-slate-800/60 bg-slate-900/40', className)}>
            <CardContent className="flex flex-col items-center justify-center py-14 px-6 text-center">
                <div className="mb-5 rounded-full bg-slate-800/60 p-4">
                    <Icon className="h-8 w-8 text-slate-400" />
                </div>

                <h3 className="text-base font-semibold text-white mb-2">
                    {config.title}
                </h3>

                <p className="text-sm text-slate-400 max-w-sm mb-6 leading-relaxed">
                    {config.description}
                </p>

                <div className="flex flex-col sm:flex-row gap-3">
                    <Link href={config.primaryAction.href}>
                        <Button className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium px-5">
                            <config.primaryAction.icon className="h-4 w-4 mr-2" />
                            {config.primaryAction.label}
                        </Button>
                    </Link>

                    {config.secondaryAction && (
                        <Link href={config.secondaryAction.href}>
                            <Button
                                variant="outline"
                                className="border-slate-700 text-slate-300 hover:bg-slate-800/50 hover:text-white"
                            >
                                <config.secondaryAction.icon className="h-4 w-4 mr-2" />
                                {config.secondaryAction.label}
                            </Button>
                        </Link>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

interface NextActionCardProps {
    title: string;
    description: string;
    actionLabel: string;
    actionHref: string;
    className?: string;
}

export function NextActionCard({
    title,
    description,
    actionLabel,
    actionHref,
    className
}: NextActionCardProps) {
    return (
        <Card className={cn('border-amber-500/20 bg-amber-500/5', className)}>
            <CardContent className="flex items-center justify-between p-4">
                <div className="flex-1">
                    <p className="font-medium text-amber-400 text-sm">{title}</p>
                    <p className="text-slate-400 text-sm">{description}</p>
                </div>
                <Link href={actionHref}>
                    <Button
                        size="sm"
                        className="bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20"
                    >
                        {actionLabel}
                        <ArrowRight className="h-4 w-4 ml-1" />
                    </Button>
                </Link>
            </CardContent>
        </Card>
    );
}
