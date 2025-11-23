'use client';

import { useState } from 'react';
import { HelpCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import type { ScanResult } from '@/lib/types';
import { chatExplain } from '@/lib/api';

interface ExplainResultButtonProps {
  scan: ScanResult;
}

export function ExplainResultButton({ scan }: ExplainResultButtonProps) {
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);

  const handleExplain = async () => {
    if (explanation) {
      // Toggle explanation visibility
      setExplanation(null);
      return;
    }

    setLoading(true);
    try {
      const prompt = `Explain this risk report for a non-technical founder and suggest next steps. 
      
Domain: ${scan.domain}
Risk Score: ${scan.risk_score}/100
Breach Likelihood (30d): ${(scan.breach_likelihood_30d * 100).toFixed(0)}%
Breach Likelihood (90d): ${(scan.breach_likelihood_90d * 100).toFixed(0)}%

Summary: ${scan.summary}

Top Issues:
${scan.signals
  .filter((s) => s.severity === 'high')
  .slice(0, 5)
  .map((s) => `- ${s.detail}`)
  .join('\n')}`;

      const response = await chatExplain(prompt);
      setExplanation(response.message);
    } catch (error) {
      toast.error('Failed to generate explanation. Please try again.');
      console.error('Explain error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <button
        onClick={handleExplain}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating explanation...
          </>
        ) : (
          <>
            <HelpCircle className="h-4 w-4" />
            {explanation ? 'Hide explanation' : 'Explain this result'}
          </>
        )}
      </button>
      {explanation && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          <p className="whitespace-pre-wrap leading-relaxed">{explanation}</p>
        </div>
      )}
    </div>
  );
}

