'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMemo } from 'react';

import { scanRequestSchema, type ScanRequestSchema } from '@/schemas/scan';
import { useScanMutation } from '@/hooks/useScanMutation';
import type { ScanResult } from '@/lib/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface DomainFormProps {
  onResult: (result: ScanResult) => void;
}

export function DomainForm({ onResult }: DomainFormProps) {
  const form = useForm<ScanRequestSchema>({
    resolver: zodResolver(scanRequestSchema),
    defaultValues: { domain: '', github_org: '' },
    mode: 'onChange',
  });
  const { handleSubmit, register, formState } = form;
  const mutation = useScanMutation(onResult);

  const disabled = useMemo(() => mutation.isPending || !formState.isValid, [mutation.isPending, formState.isValid]);

  const onSubmit = handleSubmit((values) => {
    mutation.mutate({
      domain: values.domain,
      github_org: values.github_org ? values.github_org : undefined,
    });
  });

  return (
    <form className="space-y-6 rounded-2xl bg-white/90 p-8 shadow-card" onSubmit={onSubmit}>
      <div>
        <label className="text-sm font-semibold text-slate-600">Domain</label>
        <input
          {...register('domain')}
          placeholder="example.com"
          className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-cyan-400 focus:outline-none"
        />
        {formState.errors.domain && (
          <p className="mt-1 text-sm text-rose-600">{formState.errors.domain.message}</p>
        )}
      </div>
      <div>
        <label className="text-sm font-semibold text-slate-600">GitHub Org (optional)</label>
        <input
          {...register('github_org')}
          placeholder="acme"
          className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-cyan-400 focus:outline-none"
        />
        {formState.errors.github_org && (
          <p className="mt-1 text-sm text-rose-600">{formState.errors.github_org.message}</p>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled}
        className="inline-flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-3 text-white shadow-lg shadow-slate-900/30 transition focus:outline-none focus:ring-2 focus:ring-cyan-300 disabled:opacity-50"
      >
        {mutation.isPending ? (
          <span className="flex items-center gap-2">
            <LoadingSpinner size="sm" /> Scanning…
          </span>
        ) : (
          'Run Scan'
        )}
      </button>
    </form>
  );
}
