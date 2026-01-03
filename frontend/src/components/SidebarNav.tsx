'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  LayoutDashboard,
  Settings,
  Menu,
  Activity,
  Calendar,
  Server,
  Shield,
  Bot
} from 'lucide-react';
import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { motion } from 'framer-motion';

const navItems = [
  {
    title: 'Overview',
    href: '/app/overview',
    icon: LayoutDashboard,
    description: 'Organization security posture',
  },
  {
    title: 'Assets',
    href: '/app/assets',
    icon: Server,
    description: 'Manage your assets',
  },
  {
    title: 'AI Security',
    href: '/app/ai-security',
    icon: Bot,
    description: 'AI exposure monitoring',
  },
  {
    title: 'Scans',
    href: '/app/scans',
    icon: Activity,
    description: 'View all assessments',
  },
  {
    title: 'Horizon',
    href: '/app/horizon',
    icon: Calendar,
    description: 'Weekly security brief',
  },
  {
    title: 'Settings',
    href: '/app/settings',
    icon: Settings,
    description: 'Configure preferences',
  },
];

interface SidebarNavProps {
  className?: string;
  isCollapsed?: boolean;
}

export function SidebarNav({ className, isCollapsed = false }: SidebarNavProps) {
  const pathname = usePathname();

  return (
    <TooltipProvider delayDuration={0}>
      <nav className={cn('grid gap-1', className)}>
        {navItems.map((item) => {
          const Icon = item.icon;
          // Exact match for overview, prefix for others
          const isActive = item.href === '/app/overview'
            ? pathname === '/app/overview' || pathname === '/app'
            : pathname?.startsWith(item.href);

          const linkContent = (
            <motion.span
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                'group flex items-center rounded-lg transition-all',
                isCollapsed ? 'justify-center p-2.5' : 'px-3 py-2.5',
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
              )}
            >
              <Icon className={cn(
                'flex-shrink-0 transition-colors',
                isCollapsed ? 'h-5 w-5' : 'h-4 w-4',
                isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'
              )} />

              {!isCollapsed && (
                <span className="ml-3 text-sm font-medium">{item.title}</span>
              )}
            </motion.span>
          );

          if (isCollapsed) {
            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>
                  <Link href={item.href}>{linkContent}</Link>
                </TooltipTrigger>
                <TooltipContent side="right" className="flex flex-col gap-1 bg-slate-900 border-slate-800">
                  <span className="font-medium text-white">{item.title}</span>
                  <span className="text-xs text-slate-400">{item.description}</span>
                </TooltipContent>
              </Tooltip>
            );
          }

          return (
            <Link key={item.href} href={item.href}>
              {linkContent}
            </Link>
          );
        })}
      </nav>
    </TooltipProvider>
  );
}

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle Menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 bg-slate-950 border-slate-800 p-0">
        <div className="flex h-14 items-center border-b border-slate-800 px-6">
          <Link
            href="/"
            className="flex items-center gap-2"
            onClick={() => setOpen(false)}
          >
            <Shield className="h-6 w-6 text-cyan-400" />
            <span className="font-bold text-lg text-white">ThreatVeil</span>
          </Link>
        </div>
        <div className="p-4">
          <SidebarNav />
        </div>
      </SheetContent>
    </Sheet>
  );
}
