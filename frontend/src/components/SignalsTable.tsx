'use client';

import { useState, useMemo } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { SectionHeader, SeverityBadge, SourceBadge, EmptyState } from '@/components/ui-kit';
import type { Signal, Category, Severity } from '@/lib/types';
import {
  Globe, Shield, Bug, GitBranch, Activity, Brain, ShieldAlert, Server, Database,
  Filter, Copy, Check, ExternalLink, Info, ChevronDown, Clock
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface SignalsTableProps {
  signals: Signal[];
}

type TabFilter = 'all' | 'high' | 'medium' | 'low' | 'ai' | 'external' | 'vulns';

const SOURCE_ICONS: Record<string, { icon: typeof Globe; label: string }> = {
  'https': { icon: Globe, label: 'HTTP/TLS' },
  'http': { icon: Globe, label: 'HTTP' },
  'tls': { icon: Shield, label: 'TLS/SSL' },
  'dns': { icon: Server, label: 'DNS' },
  'ct': { icon: Database, label: 'Cert Transparency' },
  'vulners': { icon: Bug, label: 'CVE Database' },
  'github': { icon: GitBranch, label: 'GitHub' },
  'otx': { icon: Activity, label: 'AlienVault OTX' },
  'lakera': { icon: Brain, label: 'AI Guardrails' },
  'ai_guard': { icon: ShieldAlert, label: 'AI Security' },
};

const CATEGORY_LABELS: Record<Category, string> = {
  'network': 'External Security',
  'software': 'Software & CVEs',
  'data_exposure': 'Data Exposure',
  'ai_integration': 'AI Exposure',
};

const FIX_RECOMMENDATIONS: Record<string, { fix: string; effort: string }> = {
  'cve': { fix: 'Apply vendor patch', effort: '1-2 hrs' },
  'vulners': { fix: 'Apply vendor patch', effort: '1-2 hrs' },
  'tls': { fix: 'Update certificate', effort: '30 min' },
  'dns': { fix: 'Review DNS records', effort: '15 min' },
  'ct': { fix: 'Audit cert issuance', effort: '30 min' },
  'github': { fix: 'Rotate credentials', effort: '1 hr' },
  'http': { fix: 'Restrict access', effort: '30 min' },
  'https': { fix: 'Review exposure', effort: '30 min' },
  'ai_guard': { fix: 'Audit AI access', effort: '1 hr' },
  'lakera': { fix: 'Review AI guardrails', effort: '1 hr' },
  'otx': { fix: 'Investigate threat', effort: '1-2 hrs' },
};

const DEFAULT_FIX = { fix: 'Investigate finding', effort: 'Varies' };

const TABS: { key: TabFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
  { key: 'ai', label: 'AI' },
  { key: 'external', label: 'External' },
  { key: 'vulns', label: 'Vulns' },
];

export function SignalsTable({ signals }: SignalsTableProps) {
  const [activeTab, setActiveTab] = useState<TabFilter>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filter signals based on active tab
  const filteredSignals = useMemo(() => {
    switch (activeTab) {
      case 'high':
        return signals.filter(s => s.severity === 'high');
      case 'medium':
        return signals.filter(s => s.severity === 'medium');
      case 'low':
        return signals.filter(s => s.severity === 'low');
      case 'ai':
        return signals.filter(s => s.category === 'ai_integration' || s.evidence.source === 'lakera' || s.evidence.source === 'ai_guard');
      case 'external':
        return signals.filter(s => s.category === 'network' || ['http', 'https', 'tls', 'dns'].includes(s.evidence.source));
      case 'vulns':
        return signals.filter(s => s.category === 'software' || ['vulners', 'cve'].includes(s.evidence.source));
      default:
        return signals;
    }
  }, [signals, activeTab]);

  // Tab counts
  const tabCounts = useMemo(() => ({
    all: signals.length,
    high: signals.filter(s => s.severity === 'high').length,
    medium: signals.filter(s => s.severity === 'medium').length,
    low: signals.filter(s => s.severity === 'low').length,
    ai: signals.filter(s => s.category === 'ai_integration' || s.evidence.source === 'lakera' || s.evidence.source === 'ai_guard').length,
    external: signals.filter(s => s.category === 'network' || ['http', 'https', 'tls', 'dns'].includes(s.evidence.source)).length,
    vulns: signals.filter(s => s.category === 'software' || ['vulners', 'cve'].includes(s.evidence.source)).length,
  }), [signals]);

  const handleCopyFix = async (signal: Signal) => {
    const fixRec = FIX_RECOMMENDATIONS[signal.evidence.source] || FIX_RECOMMENDATIONS[signal.type] || DEFAULT_FIX;
    await navigator.clipboard.writeText(`${fixRec.fix} - ${signal.detail}`);
    setCopiedId(signal.id);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div className="space-y-4">
        {/* Tabs */}
        <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-lg border border-slate-800/50 overflow-x-auto">
          {TABS.map((tab) => (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'h-8 text-xs font-medium whitespace-nowrap transition-all',
                activeTab === tab.key
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              )}
            >
              {tab.label}
              {tabCounts[tab.key] > 0 && (
                <span className={cn(
                  'ml-1.5 px-1.5 py-0.5 rounded text-2xs',
                  activeTab === tab.key ? 'bg-slate-600' : 'bg-slate-800'
                )}>
                  {tabCounts[tab.key]}
                </span>
              )}
            </Button>
          ))}
        </div>

        {/* Table */}
        <div className="rounded-xl border border-slate-800/60 bg-[#111827]/60 overflow-hidden">
          {filteredSignals.length > 0 ? (
            <Table>
              <TableHeader className="bg-slate-900/50 border-b border-slate-800/50">
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[60px] text-slate-400 font-medium">Source</TableHead>
                  <TableHead className="w-[90px] text-slate-400 font-medium">Severity</TableHead>
                  <TableHead className="text-slate-400 font-medium">Finding</TableHead>
                  <TableHead className="w-[130px] text-slate-400 font-medium">Fix</TableHead>
                  <TableHead className="w-[70px] text-slate-400 font-medium">Effort</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence mode="popLayout">
                  {filteredSignals.map((signal, idx) => {
                    const sourceConfig = SOURCE_ICONS[signal.evidence.source] || SOURCE_ICONS['http'];
                    const SourceIcon = sourceConfig.icon;
                    const fixRec = FIX_RECOMMENDATIONS[signal.evidence.source] || FIX_RECOMMENDATIONS[signal.type] || DEFAULT_FIX;
                    const isExpanded = expandedId === signal.id;

                    return (
                      <motion.tr
                        key={signal.id}
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className={cn(
                          'group border-slate-800/30 transition-colors',
                          isExpanded ? 'bg-slate-800/20' : 'hover:bg-white/[0.02]'
                        )}
                      >
                        <TableCell className="py-3">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-400 group-hover:text-white group-hover:border-slate-600/50 transition-colors cursor-help">
                                <SourceIcon className="h-4 w-4" />
                              </div>
                            </TooltipTrigger>
                            <TooltipContent className="bg-slate-900 border-slate-700">
                              <p className="font-medium">{sourceConfig.label}</p>
                              {signal.evidence.url && (
                                <p className="text-xs text-slate-400 mt-1">{signal.evidence.url}</p>
                              )}
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                        <TableCell className="py-3">
                          <SeverityBadge severity={signal.severity} size="sm" />
                        </TableCell>
                        <TableCell className="py-3">
                          <div className="space-y-1">
                            <p className="text-sm text-slate-200 leading-relaxed line-clamp-2">
                              {signal.detail}
                            </p>
                            <div className="flex items-center gap-2 text-2xs text-slate-500">
                              <span className="bg-slate-800/60 px-1.5 py-0.5 rounded">
                                {CATEGORY_LABELS[signal.category]}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {format(new Date(signal.evidence.observed_at), 'MMM d')}
                              </span>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="py-3">
                          <span className="text-sm text-cyan-400 font-medium">
                            {fixRec.fix}
                          </span>
                        </TableCell>
                        <TableCell className="py-3 text-xs text-slate-500">
                          {fixRec.effort}
                        </TableCell>
                        <TableCell className="py-3">
                          <div className="flex items-center gap-1">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopyFix(signal)}
                                  className="h-7 w-7 p-0 text-slate-500 hover:text-cyan-400"
                                >
                                  {copiedId === signal.id ? (
                                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" />
                                  )}
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent className="bg-slate-900 border-slate-700">
                                Copy fix recommendation
                              </TooltipContent>
                            </Tooltip>

                            {signal.evidence.url && (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <a
                                    href={signal.evidence.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-7 w-7 p-0 text-slate-500 hover:text-cyan-400"
                                    >
                                      <ExternalLink className="h-3.5 w-3.5" />
                                    </Button>
                                  </a>
                                </TooltipTrigger>
                                <TooltipContent className="bg-slate-900 border-slate-700">
                                  View source
                                </TooltipContent>
                              </Tooltip>
                            )}
                          </div>
                        </TableCell>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              variant="compact"
              icon="search"
              title="No signals found"
              description="No signals match the selected filter. Try a different category."
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center text-xs text-slate-500">
          <p>
            Showing {filteredSignals.length} of {signals.length} signals
          </p>
          <p>
            Each finding represents a publicly visible security signal
          </p>
        </div>
      </div>
    </TooltipProvider>
  );
}
