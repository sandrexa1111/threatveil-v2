import { ScoreBadge } from '@/components/ScoreBadge';
import { CategoryBars } from '@/components/CategoryBars';
import { SignalsTable } from '@/components/SignalsTable';
import { DownloadPdfButton } from '@/components/DownloadPdfButton';
import { PartialFailureBanner } from '@/components/PartialFailureBanner';
import { ExplainResultButton } from '@/components/ExplainResultButton';
import type { ScanResult } from '@/lib/types';
import { formatPercent, formatDate } from '@/lib/format';

interface RiskCardProps {
  result: ScanResult;
}

export function RiskCard({ result }: RiskCardProps) {
  return (
    <section className="space-y-8 rounded-3xl bg-white/90 p-8 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <ScoreBadge value={result.risk_score} />
          <p className="mt-4 text-2xl font-semibold text-slate-900">{result.domain}</p>
          <p className="text-sm text-slate-500">Last scan {formatDate(result.created_at)}</p>
        </div>
        <div className="text-right text-sm text-slate-600">
          <p>
            Breach likelihood 30d: <span className="font-semibold text-slate-900">{formatPercent(result.breach_likelihood_30d)}</span>
          </p>
          <p>
            90d: <span className="font-semibold text-slate-900">{formatPercent(result.breach_likelihood_90d)}</span>
          </p>
        </div>
        <DownloadPdfButton scan={result} />
      </div>
      <PartialFailureBanner signals={result.signals} />
      <p className="text-lg text-slate-700">{result.summary}</p>
      <ExplainResultButton scan={result} />
      <CategoryBars categories={result.categories} />
      <SignalsTable signals={result.signals} />
    </section>
  );
}
