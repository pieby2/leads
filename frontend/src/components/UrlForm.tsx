'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ingestVideos } from '@/lib/api';

function isValidYouTubeUrl(url: string): boolean {
  return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/i.test(url);
}

function isValidInstagramUrl(url: string): boolean {
  return /^https?:\/\/(www\.)?instagram\.com\/(reel|p)\/.+/i.test(url);
}

const LOCAL_PROXY = "http://localhost:8765";

async function isProxyAlive(): Promise<boolean> {
  try {
    await fetch(`${LOCAL_PROXY}/scrape`, {
      method: "OPTIONS",
      // AbortSignal.timeout is supported in modern browsers
      signal: AbortSignal.timeout ? AbortSignal.timeout(1000) : undefined,
    });
    return true;
  } catch {
    return false;
  }
}

export default function UrlForm() {
  const router = useRouter();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proxyStatus, setProxyStatus] = useState<"checking"|"online"|"offline">("checking");

  useEffect(() => {
    let mounted = true;
    const checkProxy = async () => {
      const alive = await isProxyAlive();
      if (mounted) setProxyStatus(alive ? "online" : "offline");
    };
    
    checkProxy();
    const interval = setInterval(checkProxy, 10000); // poll every 10s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // validation
    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube video URL');
      return;
    }

    if (!isValidYouTubeUrl(youtubeUrl)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    if (instagramUrl.trim() && !isValidInstagramUrl(instagramUrl)) {
      setError('Please enter a valid Instagram Reel URL');
      return;
    }

    setLoading(true);

    try {
      if (instagramUrl.trim() && proxyStatus === 'online') {
        const resp = await fetch(`${LOCAL_PROXY}/scrape`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: instagramUrl.trim(), video_id: "B" }),
        });
        if (!resp.ok) {
           throw new Error("Local proxy failed to scrape Instagram");
        }
      }

      const response = await ingestVideos(youtubeUrl.trim(), instagramUrl.trim());
      router.push(`/session/${response.session_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start analysis. Please try again.');
      setLoading(false);
    }
  };

  return (
    <form className="url-form glass-card" onSubmit={handleSubmit}>
      <div style={{ textAlign: 'center' }}>
        <div className={`proxy-badge ${proxyStatus}`} style={{ 
            fontSize: '0.8rem', 
            padding: '6px 12px', 
            borderRadius: '20px', 
            marginBottom: '16px',
            display: 'inline-block',
            backgroundColor: proxyStatus === 'online' ? 'rgba(34, 197, 94, 0.15)' : proxyStatus === 'checking' ? 'rgba(255,255,255,0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: proxyStatus === 'online' ? '#4ade80' : proxyStatus === 'checking' ? '#ccc' : '#f87171',
            border: `1px solid ${proxyStatus === 'online' ? 'rgba(34, 197, 94, 0.3)' : proxyStatus === 'checking' ? 'rgba(255,255,255,0.2)' : 'rgba(239, 68, 68, 0.2)'}`
        }}>
          {proxyStatus === "checking" && "⏳ Checking local proxy..."}
          {proxyStatus === "online" && "🟢 Local proxy running (IG unblocked)"}
          {proxyStatus === "offline" && "🔴 Local proxy offline (IG may fail)"}
        </div>
      </div>

      <div className="input-group">
        <label className="input-label">YouTube Video URL</label>
        <div style={{ position: 'relative' }}>
          <span className="url-input-icon">▶</span>
          <input
            type="url"
            className={`input-field ${error?.toLowerCase().includes('youtube') ? 'input-error' : ''}`}
            placeholder="https://youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={e => setYoutubeUrl(e.target.value)}
            disabled={loading}
            style={{ paddingLeft: 40 }}
          />
        </div>
      </div>

      <div className="form-divider">vs</div>

      <div className="input-group">
        <label className="input-label">Instagram Reel URL (Optional)</label>
        <div style={{ position: 'relative' }}>
          <span className="url-input-icon">📷</span>
          <input
            type="url"
            className={`input-field ${error?.toLowerCase().includes('instagram') ? 'input-error' : ''}`}
            placeholder="https://instagram.com/reel/..."
            value={instagramUrl}
            onChange={e => setInstagramUrl(e.target.value)}
            disabled={loading}
            style={{ paddingLeft: 40 }}
          />
        </div>
      </div>

      {error && <p className="error-text" style={{ marginBottom: 12 }}>{error}</p>}

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner spinner-inline" />
            Analyzing...
          </>
        ) : (
          'Compare Videos →'
        )}
      </button>
    </form>
  );
}
