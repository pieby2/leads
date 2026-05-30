import type { Metadata } from 'next';
import './globals.css';
import Providers from '@/components/Providers';

export const metadata: Metadata = {
  title: 'VidCompare — AI Video Analysis',
  description: 'Compare YouTube and Instagram videos side-by-side with AI-powered analysis. Get engagement insights, hook comparisons, and actionable recommendations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a0f" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        <Providers>
          <div className="page-wrapper">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
