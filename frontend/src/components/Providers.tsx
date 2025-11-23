'use client';

import { ReactNode, useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';

import { queryClient } from '@/lib/queryClient';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [client] = useState(() => queryClient);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
