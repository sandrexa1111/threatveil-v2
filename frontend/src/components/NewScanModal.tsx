'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Globe, Loader2, Search, ShieldCheck, AlertCircle } from 'lucide-react';
import { createScan } from '@/lib/api/scans';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface NewScanModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function NewScanModal({ open, onOpenChange }: NewScanModalProps) {
    const router = useRouter();
    const [domain, setDomain] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!domain.trim()) {
            setError('Please enter a domain');
            return;
        }

        // Basic domain validation
        const domainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-_.]+\.[a-zA-Z]{2,}$/;
        if (!domainPattern.test(domain.trim())) {
            setError('Please enter a valid domain (e.g., example.com)');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await createScan({ domain: domain.trim() });
            toast.success('Scan completed successfully');
            onOpenChange(false);
            setDomain('');
            router.push(`/app/scans/${result.id}`);
        } catch (err) {
            console.error('Scan failed:', err);
            setError('Failed to start scan. Please try again.');
            toast.error('Scan failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleOpenChange = (newOpen: boolean) => {
        if (!loading) {
            onOpenChange(newOpen);
            if (!newOpen) {
                setDomain('');
                setError(null);
            }
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="sm:max-w-md bg-slate-950 border-slate-800">
                <DialogHeader>
                    <DialogTitle className="text-white flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-cyan-500/10">
                            <ShieldCheck className="h-5 w-5 text-cyan-400" />
                        </div>
                        New Risk Assessment
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Enter a domain to analyze external risks and AI exposures using passive OSINT.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                    <div className="space-y-2">
                        <Label htmlFor="domain" className="text-slate-300 text-sm">
                            Domain
                        </Label>
                        <div className="relative">
                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                            <Input
                                id="domain"
                                placeholder="example.com"
                                value={domain}
                                onChange={(e) => {
                                    setDomain(e.target.value);
                                    setError(null);
                                }}
                                disabled={loading}
                                className={cn(
                                    'pl-10 h-11 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500',
                                    'focus-visible:ring-cyan-500 focus-visible:border-cyan-500/50',
                                    error && 'border-red-500/50 focus-visible:ring-red-500'
                                )}
                            />
                        </div>

                        <AnimatePresence>
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="flex items-center gap-1.5 text-red-400 text-sm"
                                >
                                    <AlertCircle className="h-3.5 w-3.5" />
                                    {error}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => handleOpenChange(false)}
                            disabled={loading}
                            className="flex-1 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={loading || !domain.trim()}
                            className="flex-1 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Search className="mr-2 h-4 w-4" />
                                    Analyze Risk
                                </>
                            )}
                        </Button>
                    </div>

                    <p className="text-xs text-slate-500 text-center pt-2">
                        We use passive signals only. No intrusive scanning of the target.
                    </p>
                </form>
            </DialogContent>
        </Dialog>
    );
}
