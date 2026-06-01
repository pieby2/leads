'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

export default function SuccessPage() {
  const router = useRouter();
  const { data: session, update } = useSession();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Force a session update so NextAuth grabs the new tier if they re-login, or we just trust the backend.
    update();
    
    // Redirect to dashboard after 3 seconds
    const timer = setTimeout(() => {
      router.push('/compare/hosted');
    }, 3000);
    
    return () => clearTimeout(timer);
  }, [router, update]);

  if (!mounted) return null;

  return (
    <div className="landing-page" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="feature-card glass-card" style={{ textAlign: 'center', padding: '4rem', maxWidth: '500px' }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
        <h2>Payment Successful!</h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
          Welcome to Pro Creator. You now have unlimited access.
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2rem' }}>
          Redirecting you to the dashboard...
        </p>
      </div>
    </div>
  );
}
