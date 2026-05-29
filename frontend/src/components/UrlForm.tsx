'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { ingestVideos } from '@/lib/api';

function isValidYouTubeUrl(url: string): boolean {
  return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/i.test(url);
}

function isValidInstagramUrl(url: string): boolean {
  return /^https?:\/\/(www\.)?instagram\.com\/(reel|p)\/.+/i.test(url);
}

export default function UrlForm() {
  const router = useRouter();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // validation
    if (!youtubeUrl.trim() || !instagramUrl.trim()) {
      setError('Please enter both URLs');
      return;
    }

    if (!isValidYouTubeUrl(youtubeUrl)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    if (!isValidInstagramUrl(instagramUrl)) {
      setError('Please enter a valid Instagram Reel URL');
      return;
    }

    setLoading(true);

    try {
      const response = await ingestVideos(youtubeUrl.trim(), instagramUrl.trim());
      router.push(`/session/${response.session_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start analysis. Please try again.');
      setLoading(false);
    }
  };

  return (
    <form className="url-form glass-card" onSubmit={handleSubmit}>
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
        <label className="input-label">Instagram Reel URL</label>
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
