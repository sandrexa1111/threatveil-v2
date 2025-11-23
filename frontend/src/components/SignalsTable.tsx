import type { Signal } from '@/lib/types';
import { categoryLabel, formatDate } from '@/lib/format';

interface SignalsTableProps {
  signals: Signal[];
}

const badgeClasses = {
  high: 'bg-rose-100 text-rose-700',
  medium: 'bg-amber-100 text-amber-800',
  low: 'bg-emerald-100 text-emerald-700',
};

export function SignalsTable({ signals }: SignalsTableProps) {
  if (!signals.length) {
    return <p className="text-sm text-slate-500">No signals yet.</p>;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-left">
        <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <tr>
            <th className="px-4 py-3">Detail</th>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">Observed</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
          {signals.map((signal) => (
            <tr key={signal.id}>
              <td className="px-4 py-3">
                <p className="font-medium text-slate-900">{signal.detail}</p>
                <p className="text-xs text-slate-500">{signal.type}</p>
              </td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ${badgeClasses[signal.severity]}`}>
                  {signal.severity}
                </span>
              </td>
              <td className="px-4 py-3">{categoryLabel(signal.category)}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{formatDate(signal.evidence.observed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
