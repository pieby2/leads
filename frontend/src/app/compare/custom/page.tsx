'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import UrlForm from '@/components/UrlForm';

export default function CustomComparePage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  if (status === 'unauthenticated' || (status === 'authenticated' && !(session as any)?.youtubeAccessToken)) {
    return (
      <div className="landing-page" style={{ minHeight: '100vh', paddingTop: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="feature-card glass-card" style={{ padding: '4rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', maxWidth: '600px' }}>
          <div className="feature-icon feature-icon-purple" style={{ marginBottom: '1rem' }}>📺</div>
          <h2 style={{ marginBottom: '1rem' }}>Connect YouTube to Continue</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            We need read-only access to YouTube to securely fetch video metadata and bypass standard API rate limits.
          </p>
          <button 
            className="btn-primary"
            onClick={() => import('next-auth/react').then(({ signIn }) => signIn('google', { callbackUrl: '/compare/custom' }))}
          >
            Connect YouTube Account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="landing-page" style={{ minHeight: '100vh', paddingTop: '100px' }}>
      <div className="container" style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        <h1 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Bring Your Own Key</h1>
        <p className="hero-subtitle" style={{ marginBottom: '3rem' }}>
          Compare videos using your own Google Gemini API key. No usage limits from our side.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <UrlForm mode="custom" />
        </div>
      </div>
    </div>
  );
}
