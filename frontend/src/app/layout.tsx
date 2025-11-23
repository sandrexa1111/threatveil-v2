import type { Metadata } from 'next';
import './globals.css';
import '@/styles/shadcn.css';

import { Providers } from '@/components/Providers';
import { Toaster } from '@/components/Toaster';

const appName = process.env.NEXT_PUBLIC_APP_NAME || 'ThreatVeilAI';

export const metadata: Metadata = {
  title: appName,
  description: 'Passive AI risk reports for SMBs.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
