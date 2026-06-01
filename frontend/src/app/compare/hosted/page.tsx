'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import UrlForm from '@/components/UrlForm';

export default function HostedComparePage() {
  const { status } = useSession();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  if (status === 'unauthenticated') {
    return (
      <div className="landing-page" style={{ minHeight: '100vh', paddingTop: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="feature-card glass-card" style={{ padding: '4rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', maxWidth: '600px' }}>
          <div className="feature-icon feature-icon-purple" style={{ marginBottom: '1rem' }}>📺</div>
          <h2 style={{ marginBottom: '1rem' }}>Connect YouTube to Continue</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            We need your YouTube account to verify your subscription and securely fetch video metadata for analysis.
          </p>
          <button 
            className="btn-primary"
            onClick={() => import('next-auth/react').then(({ signIn }) => signIn('google', { callbackUrl: '/compare/hosted' }))}
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
        <h1 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Compare Video AI</h1>
        <p className="hero-subtitle" style={{ marginBottom: '3rem' }}>
          Drop your URLs below to instantly generate deep insights and chat with our AI.
        </p>
        
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <UrlForm mode="hosted" />
        </div>
      </div>
    </div>
  );
}
