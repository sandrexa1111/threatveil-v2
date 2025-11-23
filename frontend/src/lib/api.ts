import type { ScanRequestSchema } from '@/schemas/scan';
import type { ScanResponse, ScanResult } from '@/lib/types';

const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || 'Request failed');
  }
  return res.json() as Promise<T>;
}

export async function ping(): Promise<boolean> {
  try {
    const res = await fetch(`${baseUrl}/api/ping`);
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data?.ok);
  } catch (error) {
    return false;
  }
}

export async function scanVendor(payload: ScanRequestSchema): Promise<ScanResult> {
  const res = await fetch(`${baseUrl}/api/v1/scan/vendor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await handleResponse<ScanResponse>(res);
  return data.result;
}

export async function downloadReport(scan: ScanResult): Promise<Blob> {
  const res = await fetch(`${baseUrl}/api/v1/report/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scan }),
  });
  if (!res.ok) {
    throw new Error('Unable to generate report');
  }
  return res.blob();
}

export async function chatExplain(prompt: string): Promise<{ message: string }> {
  const res = await fetch(`${baseUrl}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  return handleResponse<{ message: string }>(res);
}
