export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

const categoryLabels: Record<string, { label: string; description: string }> = {
  network: {
    label: 'Connection Security',
    description: 'Network and connection security risks including TLS, DNS, and redirect issues',
  },
  software: {
    label: 'Website & Server Software',
    description: 'Software vulnerabilities, missing security headers, and server configuration issues',
  },
  data_exposure: {
    description: 'Risks related to public data exposure and certificate transparency',
    label: 'Public Data Exposure Risk',
  },
  ai_integration: {
    label: 'AI-Related Risks',
    description: 'AI integration security issues including exposed API keys and prompts',
  },
};

export function categoryLabel(category: string): string {
  return categoryLabels[category]?.label || category.split('_').map((part) => part[0]?.toUpperCase() + part.slice(1)).join(' ');
}

export function categoryDescription(category: string): string {
  return categoryLabels[category]?.description || '';
}
