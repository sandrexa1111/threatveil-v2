'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Container } from '@/components/layout/Container';

export function LandingHeader() {
    const handleSmoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
        e.preventDefault();
        const element = document.querySelector(href);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <header className="fixed top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur supports-[backdrop-filter]:bg-slate-950/60">
            <Container>
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Link href="/" className="flex items-center space-x-2">
                            <span className="font-bold text-xl text-white">ThreatVeil</span>
                        </Link>
                    </div>
                    <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
                        <a href="#how-it-works" onClick={(e) => handleSmoothScroll(e, '#how-it-works')} className="transition-colors hover:text-white text-slate-400 cursor-pointer">
                            How it Works
                        </a>
                        <a href="#features" onClick={(e) => handleSmoothScroll(e, '#features')} className="transition-colors hover:text-white text-slate-400 cursor-pointer">
                            Features
                        </a>
                        <a href="#comparison" onClick={(e) => handleSmoothScroll(e, '#comparison')} className="transition-colors hover:text-white text-slate-400 cursor-pointer">
                            Comparison
                        </a>
                    </nav>
                    <div className="flex items-center gap-4">
                        <Link href="/app">
                            <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-800">
                                Sign In
                            </Button>
                        </Link>
                        <Link href="/app">
                            <Button size="sm" className="bg-gradient-to-r from-purple-600 to-cyan-600 text-white hover:from-purple-700 hover:to-cyan-700">Get Started</Button>
                        </Link>
                    </div>
                </div>
            </Container>
        </header>
    );
}
