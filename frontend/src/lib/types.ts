export type Severity = 'low' | 'medium' | 'high';
export type Category = 'network' | 'software' | 'data_exposure' | 'ai_integration';
export type SignalType = 'http' | 'tls' | 'dns' | 'ct' | 'cve' | 'github' | 'otx' | 'ai_guard';

export interface Evidence {
  source: string;
  observed_at: string;
  url?: string | null;
  raw: Record<string, unknown>;
}

export interface Signal {
  id: string;
  type: SignalType;
  detail: string;
  severity: Severity;
  category: Category;
  evidence: Evidence;
}

export interface CategoryScore {
  score: number;
  weight: number;
  severity: Severity;
}

export interface ScanResult {
  id: string;
  domain: string;
  github_org?: string | null;
  risk_score: number;
  categories: Record<Category, CategoryScore>;
  signals: Signal[];
  summary: string;
  breach_likelihood_30d: number;
  breach_likelihood_90d: number;
  created_at: string;
}

export interface ScanResponse {
  result: ScanResult;
}
