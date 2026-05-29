'use client';

import { useEffect, useState } from 'react';
import UrlForm from '@/components/UrlForm';

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

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

        <p className="hero-subtitle">
          Drop a YouTube video and an Instagram Reel — our AI analyzes engagement,
          hooks, and content strategy so you can understand what works and why.
        </p>

        <div className="url-form-wrapper">
          <UrlForm />
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
