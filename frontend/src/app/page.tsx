'use client';

import { useEffect, useState } from 'react';

import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { DomainForm } from '@/components/DomainForm';
import { RiskCard } from '@/components/RiskCard';
import type { ScanResult } from '@/lib/types';
import { ping } from '@/lib/api';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function Page() {
  const [result, setResult] = useState<ScanResult | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    ping().then(setApiOk);
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 pb-16 pt-10">
      <Header />
      <section className="grid gap-8 md:grid-cols-[1fr_1.5fr]">
        <div>
          <DomainForm onResult={setResult} />
          <div className="mt-4 text-sm text-slate-500">
            API status:{' '}
            {apiOk === null ? <LoadingSpinner size="sm" /> : apiOk ? <span className="text-emerald-600">Online</span> : <span className="text-rose-600">Offline</span>}
          </div>
        </div>
        {result ? <RiskCard result={result} /> : <PlaceholderPanel />}
      </section>
      <Footer />
    </main>
  );
}

function PlaceholderPanel() {
  return (
    <div className="flex min-h-[400px] flex-col justify-center rounded-3xl border border-dashed border-slate-200 bg-white/80 p-8 text-center text-slate-500">
      <p className="text-lg font-semibold text-slate-700">Awaiting scan...</p>
      <p className="mt-2">Submit a domain to see risk scoring, signals, and exportable PDF.</p>
    </div>
  );
}
