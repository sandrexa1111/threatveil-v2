'use client';

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import type { Signal } from '@/lib/types';

interface PartialFailureBannerProps {
  signals: Signal[];
}

export function PartialFailureBanner({ signals }: PartialFailureBannerProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Filter service error signals
  const serviceErrors = signals.filter((s) => s.id.startsWith('service_') && s.id.endsWith('_failure'));
  
  if (serviceErrors.length === 0) {
    return null;
  }
  
  const serviceNames = [...new Set(serviceErrors.map((s) => s.evidence.source.toUpperCase()))].join(', ');
  
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-amber-900">
            ⚠ Some checks failed ({serviceNames}). Results may be incomplete.
          </p>
          {expanded && (
            <div className="mt-3 space-y-2 rounded-lg bg-amber-100/50 p-3 text-xs text-amber-800">
              <p className="font-semibold">Technical details:</p>
              <ul className="list-inside list-disc space-y-1">
                {serviceErrors.map((signal) => {
                  const errorMsg = signal.evidence.raw?.error;
                  return (
                    <li key={signal.id}>
                      <span className="font-medium">{signal.evidence.source.toUpperCase()}:</span> {signal.detail}
                      {errorMsg != null ? (
                        <span className="ml-2 text-amber-700">({String(errorMsg)})</span>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex-shrink-0 text-amber-700 hover:text-amber-900"
          aria-label={expanded ? 'Hide technical details' : 'Show technical details'}
        >
          {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </button>
      </div>
    </div>
  );
}

