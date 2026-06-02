'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getSession } from '@/lib/api';
import { SessionData, INGESTION_STEPS } from '@/types';
import VideoCard from '@/components/VideoCard';
import ChatPanel from '@/components/ChatPanel';
import SkeletonCard from '@/components/SkeletonCard';
import ProgressStepper from '@/components/ProgressStepper';

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const fetchSession = useCallback(async () => {
    try {
      const data = await getSession(sessionId);
      setSession(data);

      if (data.status === 'ready') {
        setCurrentStep(INGESTION_STEPS.length - 1);
        setLoading(false);
      } else if (data.status === 'processing') {
        // bump step indicator forward if still processing
        setCurrentStep(prev => Math.min(prev + 1, INGESTION_STEPS.length - 2));
      } else if (data.status === 'error') {
        setError('Something went wrong processing your videos.');
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load session');
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    let mounted = true;
    let ws: WebSocket;

    const init = async () => {
      await fetchSession();
      
      // If still not ready after initial fetch, connect to WebSocket
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://vidcompare-backend.onrender.com';
      // Local dev fallback if needed, but we'll default to prod since it's hosted
      const finalWsUrl = window.location.hostname === 'localhost' ? 'ws://localhost:8000' : wsUrl;
      
      ws = new WebSocket(`${finalWsUrl}/api/v1/ws/session/${sessionId}`);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.status === 'ready') {
            fetchSession();
          } else if (data.status === 'error') {
            setError(data.step || 'Something went wrong processing your videos.');
            setLoading(false);
          } else {
            const p = data.progress || 0;
            const mappedStep = Math.floor((p / 100) * (INGESTION_STEPS.length - 1));
            setCurrentStep(mappedStep);
          }
        } catch (e) {
          console.error(e);
        }
      };
    };

    init();

    return () => {
      mounted = false;
      if (ws) ws.close();
    };
  }, [sessionId]);

  // TODO: maybe add a timeout after 2 min if it's still loading

  if (error) {
    return (
      <div className="session-page">
        <div className="container">
          <header className="session-header">
            <div className="session-logo" onClick={() => router.push('/')} style={{ cursor: 'pointer' }}>
              <span>VidCompare</span>
            </div>
          </header>
          <div className="error-container">
            <div className="error-icon">😵</div>
            <h2 className="error-title">Something went wrong</h2>
            <p className="error-description">{error}</p>
            <button className="btn-primary" onClick={() => router.push('/')}>
              ← Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="session-page">
      <div className="container">
        <header className="session-header">
          <div className="session-logo" onClick={() => router.push('/')} style={{ cursor: 'pointer' }}>
            <span>VidCompare</span>
          </div>
          <div className="session-id-badge">
            {sessionId.slice(0, 8)}…
          </div>
        </header>

        {loading ? (
          <>
            <ProgressStepper currentStep={currentStep} />
            <div className="videos-grid animate-fade-in">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          </>
        ) : session ? (
          <div className="workspace-layout animate-fade-in">
            <div className="videos-grid">
              <VideoCard video={session.videos.A} label="A" />
              {session.videos.B && <VideoCard video={session.videos.B} label="B" />}
            </div>
            <ChatPanel sessionId={sessionId} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
