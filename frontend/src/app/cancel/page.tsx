'use client';

import { useRouter } from 'next/navigation';

export default function CancelPage() {
  const router = useRouter();

  return (
    <div className="landing-page" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="feature-card glass-card" style={{ textAlign: 'center', padding: '4rem', maxWidth: '500px' }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
        <h2>Payment Cancelled</h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '1rem', marginBottom: '2rem' }}>
          Your checkout process was cancelled. You have not been charged.
        </p>
        <button className="btn-primary" onClick={() => router.push('/pricing')}>
          Return to Pricing
        </button>
      </div>
    </div>
  );
}
