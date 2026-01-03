'use client';

import { MobileNav } from './SidebarNav';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export function TopNav() {
    return (
        <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
            <MobileNav />
            <div className="flex flex-1 items-center gap-4 md:hidden">
                <span className="font-semibold">ThreatVeil</span>
            </div>
            <div className="ml-auto flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground hidden sm:inline-block">demo@threatveil.com</span>
                    <Avatar className="h-8 w-8">
                        <AvatarImage src="/avatars/01.png" alt="@user" />
                        <AvatarFallback>TV</AvatarFallback>
                    </Avatar>
                </div>
            </div>
        </header>
    );
}
