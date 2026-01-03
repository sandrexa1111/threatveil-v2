const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

export interface ScanAIData {
  ai_score: number;
  ai_tools_detected: string[];
  ai_key_leaks: Array<{
    key_type?: string;
    repository?: string;
    path?: string;
    url?: string;
  }>;
  ai_agents_detected: string[];
  ai_summary: string;
  created_at: string | null;
}

/**
 * Fetch AI risk data for a scan.
 * Returns null if ScanAI doesn't exist (404) or on error.
 */
export async function getScanAI(scanId: string): Promise<ScanAIData | null> {
  try {
    const res = await fetch(`${baseUrl}/api/v1/scan/${scanId}/ai`);
    
    if (res.status === 404) {
      // ScanAI not created yet - this is normal, not an error
      return null;
    }
    
    if (!res.ok) {
      // Other errors - log in dev only
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to fetch ScanAI:', res.status, res.statusText);
      }
      return null;
    }
    
    const data = await res.json();
    return data as ScanAIData;
  } catch (error) {
    // Network errors - never crash UI
    if (process.env.NODE_ENV === 'development') {
      console.warn('Error fetching ScanAI:', error);
    }
    return null;
  }
}


