'use client';

import { SectionHeader, SeverityBadge } from '@/components/ui-kit';
import type { ScanResult } from '@/lib/types';
import { ShieldCheck, TrendingUp, AlertTriangle, Info } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function RiskCard({ result }: { result: ScanResult }) {
  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 30) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getRiskLevel = (score: number): 'high' | 'medium' | 'low' => {
    if (score >= 70) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
  };

  const getProgressColor = (score: number) => {
    if (score >= 70) return '#ef4444';
    if (score >= 30) return '#f59e0b';
    return '#22c55e';
  };

  // Radial gauge calculation (smaller, supporting size)
  const radius = 56;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (result.risk_score / 100) * circumference;

  return (
    <div className="rounded-xl border border-slate-800/60 bg-slate-900/40 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800/50">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-slate-400" />
          <h3 className="text-sm font-medium text-slate-300">Risk Assessment</h3>
          <SeverityBadge severity={getRiskLevel(result.risk_score)} size="sm" />
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Score Section - Compact */}
        <div className="flex items-center gap-5">
          <div className="relative flex items-center justify-center flex-shrink-0">
            <svg
              height={radius * 2}
              width={radius * 2}
              className="transform -rotate-90"
            >
              {/* Background circle */}
              <circle
                stroke="#1e293b"
                strokeWidth={stroke}
                fill="transparent"
                r={normalizedRadius}
                cx={radius}
                cy={radius}
              />
              {/* Progress circle */}
              <motion.circle
                stroke={getProgressColor(result.risk_score)}
                strokeWidth={stroke}
                strokeDasharray={circumference + ' ' + circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                strokeLinecap="round"
                fill="transparent"
                r={normalizedRadius}
                cx={radius}
                cy={radius}
              />
            </svg>

            <div className="absolute flex flex-col items-center">
              <span className={cn('text-2xl font-semibold', getRiskColor(result.risk_score))}>
                {result.risk_score}
              </span>
              <span className="text-[10px] text-slate-500 uppercase tracking-wide">
                Score
              </span>
            </div>
          </div>

          <div className="flex-1 text-sm text-slate-400 leading-relaxed">
            Reflects publicly visible exposure that could be exploited.
          </div>
        </div>

        {/* Category Breakdown - Compact */}
        <div className="space-y-3">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="h-3 w-3" />
            Contributing Factors
          </p>

          <div className="grid grid-cols-2 gap-3">
            <CategoryItem
              label="External Security"
              score={result.categories.network.score}
            />
            <CategoryItem
              label="Software & CVEs"
              score={result.categories.software.score}
            />
            <CategoryItem
              label="Data Exposure"
              score={result.categories.data_exposure.score}
            />
            {result.categories.ai_integration && (
              <CategoryItem
                label="AI Exposure"
                score={result.categories.ai_integration.score}
              />
            )}
          </div>
        </div>

        {/* Breach Likelihood - Simplified */}
        <div className="pt-4 border-t border-slate-800/50">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <TrendingUp className="h-3 w-3" />
            Breach Likelihood
          </p>
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className={cn('text-lg font-semibold', result.breach_likelihood_30d > 0.5 ? 'text-red-400' : result.breach_likelihood_30d > 0.2 ? 'text-amber-400' : 'text-emerald-400')}>
                {Math.round(result.breach_likelihood_30d * 100)}%
              </span>
              <span className="text-xs text-slate-500 ml-1">30-day</span>
            </div>
            <div>
              <span className={cn('text-lg font-semibold', result.breach_likelihood_90d > 0.5 ? 'text-red-400' : result.breach_likelihood_90d > 0.2 ? 'text-amber-400' : 'text-emerald-400')}>
                {Math.round(result.breach_likelihood_90d * 100)}%
              </span>
              <span className="text-xs text-slate-500 ml-1">90-day</span>
            </div>
          </div>
        </div>

        {/* Score explanation */}
        <WhyThisScore result={result} />
      </div>
    </div>
  );
}

function WhyThisScore({ result }: { result: ScanResult }) {
  const categories = [
    { key: 'network', label: 'External Security', score: result.categories.network?.score || 0, weight: result.categories.network?.weight || 0 },
    { key: 'software', label: 'Software & CVEs', score: result.categories.software?.score || 0, weight: result.categories.software?.weight || 0 },
    { key: 'data_exposure', label: 'Data Exposure', score: result.categories.data_exposure?.score || 0, weight: result.categories.data_exposure?.weight || 0 },
    { key: 'ai_integration', label: 'AI Exposure', score: result.categories.ai_integration?.score || 0, weight: result.categories.ai_integration?.weight || 0 },
  ].filter(c => c.score > 0 || c.weight > 0);

  const totalWeightedScore = categories.reduce((sum, c) => sum + (c.score * c.weight), 0);
  const contributions = categories.map(c => ({
    ...c,
    contribution: totalWeightedScore > 0 ? Math.round((c.score * c.weight / totalWeightedScore) * 100) : 0,
  })).sort((a, b) => b.contribution - a.contribution);

  const topDriver = contributions[0];

  if (!topDriver || topDriver.contribution <= 30) {
    return null;
  }

  return (
    <div className="pt-4 border-t border-slate-800/50">
      <div className="flex items-start gap-2 text-sm text-slate-400 bg-slate-950/30 rounded-lg p-3 border border-slate-800/50">
        <Info className="h-4 w-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          Primary driver: <span className="text-slate-300 font-medium">{topDriver.label.toLowerCase()}</span> ({topDriver.contribution}% of score).
        </p>
      </div>
    </div>
  );
}

function CategoryItem({ label, score }: { label: string, score: number }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-300 font-medium tabular-nums">{score}</span>
    </div>
  );
}
