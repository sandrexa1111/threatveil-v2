'use client';

import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

import { scanVendor } from '@/lib/api';
import type { ScanRequestSchema } from '@/schemas/scan';
import type { ScanResult } from '@/lib/types';

export function useScanMutation(onSuccess: (result: ScanResult) => void) {
  return useMutation({
    mutationFn: (payload: ScanRequestSchema) => scanVendor(payload),
    onSuccess: (data) => {
      toast.success('Scan completed');
      onSuccess(data);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Scan failed');
    },
  });
}
