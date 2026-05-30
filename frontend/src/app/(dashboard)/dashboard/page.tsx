'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { getUserSessions } from '@/lib/api';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/api/auth/signin');
    }
  }, [status, router]);

  useEffect(() => {
    if (status === 'authenticated') {
      getUserSessions()
        .then(data => {
          setSessions(data);
          setLoading(false);
        })
        .catch(err => {
          setError(err.message);
          setLoading(false);
        });
    }
  }, [status]);

  if (status === 'loading' || loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div>
      <h1>Your Sessions</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      {sessions.length === 0 && !error ? (
        <p>No sessions found. <Link href="/" style={{ color: '#0070f3' }}>Create one?</Link></p>
      ) : (
        <ul style={{ listStyleType: 'none', padding: 0 }}>
          {sessions.map(s => (
            <li key={s.id} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #333', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Link href={`/session/${s.id}`}>
                  <strong>Session: {s.id.slice(0, 8)}</strong>
                </Link>
                <span>{new Date(s.created_at).toLocaleDateString()}</span>
              </div>
              <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#ccc' }}>
                <p>Status: {s.status}</p>
                <p>Videos: {s.video_a_id} | {s.video_b_id}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
