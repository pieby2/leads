'use client';

import { useEffect, useState } from 'react';
import UrlForm from '@/components/UrlForm';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/signup');
    }
  }, [status, router]);

  if (!mounted) return null;
  if (status === 'loading' || status === 'unauthenticated') return null;


  return (
    <div className="landing-page">
      {/* Background glow effects */}
      <div className="landing-bg-glow" />
      <div className="landing-bg-glow-2" />

      {/* Hero */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          AI-Powered Video Analysis
        </div>

        <h1 className="hero-title">
          <span className="hero-title-gradient">Compare. Analyze. Grow.</span>
        </h1>

        <p className="hero-subtitle" style={{ maxWidth: '600px', margin: '0 auto 2rem' }}>
          Drop a YouTube video and an Instagram Reel — our AI analyzes engagement,
          hooks, and content strategy so you can understand what works and why.
        </p>

        <div className="gateway-cards" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>
          {/* Path A */}
          <div className="feature-card glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem' }}>
            <div className="feature-icon feature-icon-purple" style={{ marginBottom: '1rem' }}>🔑</div>
            <h3 style={{ marginBottom: '0.5rem' }}>Bring Your Own Key</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', flexGrow: 1 }}>
              Use your own OpenAI API key. Completely free, no usage limits.
            </p>
            <button 
              className="btn-secondary"
              onClick={() => router.push('/compare/custom')}
              style={{ width: '100%' }}
            >
              {session ? 'Go to Custom Path →' : 'Connect YouTube & Start'}
            </button>
          </div>

          {/* Path B */}
          <div className="feature-card glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem', border: '1px solid var(--primary-accent)' }}>
            <div className="feature-icon feature-icon-blue" style={{ marginBottom: '1rem' }}>⚡</div>
            <h3 style={{ marginBottom: '0.5rem' }}>Compare Video AI</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', flexGrow: 1 }}>
              Fully managed hosted AI. Monthly subscription with high usage limits.
            </p>
            <button 
              className="btn-primary"
              onClick={() => router.push('/pricing')}
              style={{ width: '100%' }}
            >
              {session ? 'View Pricing →' : 'Connect YouTube & Subscribe'}
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <div className="container">
          <div className="features-header">
            <h2>Why VidCompare?</h2>
            <p>Instant cross-platform video intelligence</p>
          </div>

          <div className="features-grid">
            <div className="feature-card glass-card">
              <div className="feature-icon feature-icon-purple">📊</div>
              <h3>Engagement Analysis</h3>
              <p>
                Compare views, likes, comments, and engagement rates
                side-by-side. See which content resonates with audiences.
              </p>
            </div>

            <div className="feature-card glass-card">
              <div className="feature-icon feature-icon-blue">🎯</div>
              <h3>Hook Comparison</h3>
              <p>
                AI breaks down the opening seconds of each video to identify
                what makes a great hook versus a missed opportunity.
              </p>
            </div>

            <div className="feature-card glass-card">
              <div className="feature-icon feature-icon-teal">💡</div>
              <h3>AI Insights Chat</h3>
              <p>
                Ask anything about the videos — content strategy, pacing,
                audience appeal. Get cited answers grounded in the actual content.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        Built with ❤️ by <span>VidCompare</span> — Powered by RAG
      </footer>
    </div>
  );
}
