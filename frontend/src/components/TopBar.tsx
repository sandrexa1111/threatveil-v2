'use client';

import { useState } from 'react';
import { Bell, Search, Plus, Building2, ChevronDown } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { NewScanModal } from './NewScanModal';

interface TopBarProps {
    isCollapsed?: boolean;
}

export function TopBar({ isCollapsed }: TopBarProps) {
    const [isNewScanOpen, setIsNewScanOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    return (
        <>
            <header className={cn(
                'sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-slate-800 bg-slate-950/95 backdrop-blur-sm px-6',
            )}>
                {/* Org Selector (Placeholder) */}
                <div className="hidden lg:flex items-center gap-2 border-r border-slate-800 pr-4">
                    <Button
                        variant="ghost"
                        className="h-9 gap-2 text-slate-300 hover:text-white hover:bg-slate-800/50"
                    >
                        <Building2 className="h-4 w-4 text-slate-500" />
                        <span className="text-sm font-medium">Demo Organization</span>
                        <ChevronDown className="h-3 w-3 text-slate-500" />
                    </Button>
                </div>

                {/* Search */}
                <div className="flex flex-1 items-center gap-4">
                    <div className="relative w-full max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input
                            type="search"
                            placeholder="Search scans, domains..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className={cn(
                                'h-9 w-full rounded-lg border-slate-800 bg-slate-900/50 pl-9',
                                'text-slate-300 placeholder:text-slate-500',
                                'focus-visible:ring-1 focus-visible:ring-cyan-500 focus-visible:border-cyan-500/50',
                                'transition-colors'
                            )}
                        />
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    {/* New Scan Button */}
                    <Button
                        onClick={() => setIsNewScanOpen(true)}
                        className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium h-9 gap-2"
                    >
                        <Plus className="h-4 w-4" />
                        <span className="hidden sm:inline">New Scan</span>
                    </Button>

                    {/* Notifications */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="relative text-slate-400 hover:text-white hover:bg-slate-800/50"
                    >
                        <Bell className="h-5 w-5" />
                        {/* Notification badge */}
                        <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-cyan-400" />
                    </Button>

                    {/* User Menu */}
                    <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
                        <div className="hidden sm:block text-right">
                            <p className="text-sm font-medium text-white">Demo User</p>
                            <p className="text-xs text-slate-500">demo@threatveil.com</p>
                        </div>
                        <Avatar className="h-9 w-9 border border-slate-700 cursor-pointer hover:border-slate-600 transition-colors">
                            <AvatarImage src="/avatars/01.png" alt="@user" />
                            <AvatarFallback className="bg-slate-800 text-cyan-400 font-medium">
                                DU
                            </AvatarFallback>
                        </Avatar>
                    </div>
                </div>
            </header>

            {/* New Scan Modal */}
            <NewScanModal
                open={isNewScanOpen}
                onOpenChange={setIsNewScanOpen}
            />
        </>
    );
}
