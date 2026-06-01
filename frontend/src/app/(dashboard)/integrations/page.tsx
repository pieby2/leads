import React from 'react';
import { getServerSession } from 'next-auth/next';
import { redirect } from 'next/navigation';

import { authOptions } from '@/lib/auth';

export default async function IntegrationsPage() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect('/api/auth/signin');
  }

  // We are currently mocking the state where tokens are checked.
  // Ideally, you'd fetch the user's profile from your backend API
  // to see if they have youtube_access_token and instagram_access_token.

  return (
    <div style={{ maxWidth: '600px' }}>
      <h1>Integrations</h1>
      <p style={{ color: '#888', marginBottom: '2rem' }}>
        Connect your accounts to enable high-capacity metadata fetching using official APIs.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ padding: '1rem', border: '1px solid #333', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: '0 0 0.5rem' }}>YouTube</h3>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#aaa' }}>Connect your YouTube account to analyze videos.</p>
          </div>
          <a 
            href={`${process.env.NEXT_PUBLIC_API_URL || 'https://vidcompare-backend.onrender.com'}/api/auth/youtube/login?token=${(session as any)?.accessToken}`} 
            style={{ padding: '0.5rem 1rem', background: '#ff0000', color: '#fff', textDecoration: 'none', borderRadius: '4px', fontWeight: 'bold' }}
          >
            Connect YouTube
          </a>
        </div>

        <div style={{ padding: '1rem', border: '1px solid #333', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: '0 0 0.5rem' }}>Instagram</h3>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#aaa' }}>Connect your Instagram account to analyze reels.</p>
          </div>
          <a 
            href={`${process.env.NEXT_PUBLIC_API_URL || 'https://vidcompare-backend.onrender.com'}/api/auth/instagram/login?token=${(session as any)?.accessToken}`} 
            style={{ padding: '0.5rem 1rem', background: '#E1306C', color: '#fff', textDecoration: 'none', borderRadius: '4px', fontWeight: 'bold' }}
          >
            Connect Instagram
          </a>
        </div>
      </div>
    </div>
  );
}
