import { CategoryScore, Category } from '@/lib/types';
import { categoryLabel, categoryDescription } from '@/lib/format';

interface CategoryBarsProps {
  categories: Record<Category, CategoryScore>;
}

export function CategoryBars({ categories }: CategoryBarsProps) {
  const entries = Object.entries(categories) as [Category, CategoryScore][];
  return (
    <div className="space-y-3">
      {entries.map(([category, data]) => (
        <div key={category}>
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span title={categoryDescription(category)} className="cursor-help">
              {categoryLabel(category)}
            </span>
            <span className="font-semibold text-slate-900">{data.score}</span>
          </div>
          <div className="mt-1 h-2 rounded-full bg-slate-200">
            <div
              className={`h-2 rounded-full ${data.severity === 'high' ? 'bg-rose-500' : data.severity === 'medium' ? 'bg-amber-400' : 'bg-emerald-400'}`}
              style={{ width: `${data.score}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
