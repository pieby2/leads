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
    router.push('/');
    return null;
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
