'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function BillingPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/api/auth/signin');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1>Billing & Subscription</h1>
      <p style={{ marginBottom: '2rem', color: '#ccc' }}>
        Manage your subscription plan and billing details.
      </p>
      
      <div style={{ padding: '1.5rem', border: '1px solid #333', borderRadius: '8px', marginBottom: '2rem' }}>
        <h2>Pro Plan</h2>
        <p>$15 / month</p>
        <ul style={{ margin: '1rem 0', paddingLeft: '1.5rem', color: '#aaa' }}>
          <li>Unlimited video comparisons</li>
          <li>Priority AI analysis</li>
          <li>Advanced chat history</li>
        </ul>
        <button 
          className="btn-primary" 
          onClick={() => alert('Redirecting to Stripe Checkout...')}
          style={{ width: '100%' }}
        >
          Subscribe to Pro
        </button>
      </div>

      <div style={{ padding: '1.5rem', border: '1px solid #333', borderRadius: '8px' }}>
        <h2>Customer Portal</h2>
        <p style={{ color: '#aaa', marginBottom: '1rem' }}>
          Update payment methods, view invoices, or cancel your subscription.
        </p>
        <button 
          className="btn-secondary" 
          onClick={() => alert('Redirecting to Stripe Customer Portal...')}
          style={{ width: '100%', padding: '0.75rem', background: '#333', border: 'none', borderRadius: '4px', color: 'white', cursor: 'pointer' }}
        >
          Manage Subscription
        </button>
      </div>
    </div>
  );
}
