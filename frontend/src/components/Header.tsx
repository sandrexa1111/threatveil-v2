'use client';

import Link from 'next/link';

export function Header() {
  return (
    <header className="flex items-center justify-between py-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-slate-500">ThreatVeilAI</p>
        <h1 className="text-3xl font-semibold text-slate-900">Passive Risk Intelligence</h1>
      </div>
      <Link
        href="https://threatveil.com"
        className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-white"
      >
        Docs
      </Link>
    </header>
  );
}
