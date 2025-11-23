import { Severity } from '@/lib/types';

interface ScoreBadgeProps {
  value: number;
}

function severityFromScore(score: number): Severity {
  if (score >= 70) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
}

const classes: Record<Severity, string> = {
  high: 'bg-rose-100 text-rose-700 border-rose-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
};

export function ScoreBadge({ value }: ScoreBadgeProps) {
  const severity = severityFromScore(value);
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${classes[severity]}`}>
      Risk {value}
    </span>
  );
}
