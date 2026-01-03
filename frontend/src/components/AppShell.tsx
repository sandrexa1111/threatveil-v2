'use client';

import { useState, createContext, useContext } from 'react';
import { SidebarNav, MobileNav } from './SidebarNav';
import { TopBar } from './TopBar';
import Link from 'next/link';
import { Shield, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';

// Context for sidebar state
interface SidebarContextType {
    isCollapsed: boolean;
    setIsCollapsed: (value: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType>({
    isCollapsed: false,
    setIsCollapsed: () => { },
});

export const useSidebar = () => useContext(SidebarContext);

export function AppShell({ children }: { children: React.ReactNode }) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed }}>
            <div className="min-h-screen w-full bg-slate-950">
                {/* Desktop Layout */}
                <div className="hidden md:flex">
                    {/* Sidebar */}
                    <motion.aside
                        initial={false}
                        animate={{ width: isCollapsed ? 72 : 280 }}
                        transition={{ duration: 0.2, ease: 'easeInOut' }}
                        className={cn(
                            'fixed left-0 top-0 h-screen border-r border-slate-800 bg-slate-950 z-40',
                            'flex flex-col'
                        )}
                    >
                        {/* Logo */}
                        <div className={cn(
                            'flex h-16 items-center border-b border-slate-800',
                            isCollapsed ? 'justify-center px-2' : 'px-6'
                        )}>
                            <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white">
                                <div className="relative">
                                    <Shield className="h-7 w-7 text-cyan-400" />
                                    <div className="absolute inset-0 blur-lg bg-cyan-400/30 rounded-full" />
                                </div>
                                <AnimatePresence>
                                    {!isCollapsed && (
                                        <motion.span
                                            initial={{ opacity: 0, width: 0 }}
                                            animate={{ opacity: 1, width: 'auto' }}
                                            exit={{ opacity: 0, width: 0 }}
                                            transition={{ duration: 0.15 }}
                                            className="overflow-hidden whitespace-nowrap"
                                        >
                                            ThreatVeil
                                        </motion.span>
                                    )}
                                </AnimatePresence>
                            </Link>
                        </div>

                        {/* Navigation */}
                        <div className="flex-1 overflow-auto py-4 px-3">
                            <SidebarNav isCollapsed={isCollapsed} />
                        </div>

                        {/* Collapse Toggle */}
                        <div className={cn(
                            'border-t border-slate-800 py-3',
                            isCollapsed ? 'px-2' : 'px-4'
                        )}>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className={cn(
                                    'text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors',
                                    isCollapsed ? 'w-full justify-center' : 'w-full justify-start'
                                )}
                            >
                                {isCollapsed ? (
                                    <ChevronRight className="h-4 w-4" />
                                ) : (
                                    <>
                                        <ChevronLeft className="h-4 w-4 mr-2" />
                                        <span className="text-xs">Collapse</span>
                                    </>
                                )}
                            </Button>
                        </div>
                    </motion.aside>

                    {/* Main Content Area */}
                    <div
                        className={cn(
                            'flex-1 flex flex-col transition-all duration-200',
                            isCollapsed ? 'ml-[72px]' : 'ml-[280px]'
                        )}
                    >
                        <TopBar isCollapsed={isCollapsed} />
                        <main className="flex-1 overflow-auto">
                            <div className="mx-auto max-w-7xl p-6 lg:p-8">
                                <motion.div
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.25 }}
                                >
                                    {children}
                                </motion.div>
                            </div>
                        </main>
                    </div>
                </div>

                {/* Mobile Layout */}
                <div className="flex flex-col md:hidden">
                    <header className="sticky top-0 z-50 flex h-14 items-center gap-4 border-b border-slate-800 bg-slate-950 px-4">
                        <MobileNav />
                        <Link href="/" className="flex items-center gap-2 font-bold text-lg text-white">
                            <Shield className="h-5 w-5 text-cyan-400" />
                            <span>ThreatVeil</span>
                        </Link>
                    </header>
                    <main className="flex-1 p-4">
                        {children}
                    </main>
                </div>
            </div>
        </SidebarContext.Provider>
    );
}
