'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function PricingPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  if (status === 'unauthenticated') {
    router.push('/');
    return null;
  }

  return (
    <div className="landing-page" style={{ minHeight: '100vh', paddingTop: '100px' }}>
      <div className="container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 className="hero-title" style={{ fontSize: '3rem' }}>Choose Your Plan</h1>
          <p className="hero-subtitle">Simple, transparent pricing for creators and agencies.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          {/* Free Tier */}
          <div className="feature-card glass-card" style={{ padding: '3rem 2rem', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Free Trial</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
              $0<span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>/mo</span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem 0', flexGrow: 1, color: 'var(--text-secondary)' }}>
              <li style={{ marginBottom: '1rem' }}>✅ 3 comparisons per month</li>
              <li style={{ marginBottom: '1rem' }}>✅ Basic Engagement Analytics</li>
              <li style={{ marginBottom: '1rem' }}>✅ 10 AI Chat Messages</li>
            </ul>
            <button 
              className="btn-secondary" 
              onClick={() => router.push('/compare/hosted')}
              style={{ width: '100%' }}
            >
              Continue Free
            </button>
          </div>

          {/* Pro Tier */}
          <div className="feature-card glass-card" style={{ padding: '3rem 2rem', display: 'flex', flexDirection: 'column', border: '2px solid var(--primary-accent)' }}>
            <div style={{ background: 'var(--primary-accent)', color: 'white', padding: '0.25rem 1rem', borderRadius: '1rem', fontSize: '0.75rem', fontWeight: 'bold', display: 'inline-block', alignSelf: 'flex-start', marginBottom: '1rem' }}>POPULAR</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Pro Creator</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
              $15<span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>/mo</span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem 0', flexGrow: 1, color: 'var(--text-secondary)' }}>
              <li style={{ marginBottom: '1rem' }}>✅ Unlimited comparisons</li>
              <li style={{ marginBottom: '1rem' }}>✅ Deep Hook Analysis</li>
              <li style={{ marginBottom: '1rem' }}>✅ Unlimited AI Chat Messages</li>
              <li style={{ marginBottom: '1rem' }}>✅ Priority Support</li>
            </ul>
            <button 
              className="btn-primary" 
              onClick={() => {
                alert('Stripe checkout would go here! Redirecting to app for now.');
                router.push('/compare/hosted');
              }}
              style={{ width: '100%' }}
            >
              Upgrade to Pro
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
