'use client';

import { useState } from 'react';
import { FileDown } from 'lucide-react';

import type { ScanResult } from '@/lib/types';
import { downloadReport } from '@/lib/api';
import { toast } from 'sonner';

interface DownloadPdfButtonProps {
  scan: ScanResult;
}

export function DownloadPdfButton({ scan }: DownloadPdfButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const blob = await downloadReport(scan);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `threatveil-${scan.domain}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Unable to download report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleDownload}
      disabled={loading}
      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-50"
    >
      <FileDown size={16} /> {loading ? 'Preparing…' : 'Download PDF'}
    </button>
  );
}
