import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import '@/styles/shadcn.css';

import { Providers } from '@/components/Providers';
import { Toaster } from '@/components/Toaster';

const inter = Inter({ subsets: ['latin'] });

const appName = process.env.NEXT_PUBLIC_APP_NAME || 'ThreatVeil';

export const metadata: Metadata = {
  title: appName,
  description: 'AI-Native Cybersecurity Intelligence for the New Era',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
