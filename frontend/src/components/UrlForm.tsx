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

export default function UrlForm() {
  const router = useRouter();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedKey = localStorage.getItem('openai_api_key');
    if (savedKey) setOpenaiApiKey(savedKey);
  }, []);

  const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setOpenaiApiKey(val);
    if (val) {
      localStorage.setItem('openai_api_key', val);
    } else {
      localStorage.removeItem('openai_api_key');
    }
  };

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
      const response = await ingestVideos(youtubeUrl.trim(), instagramUrl.trim(), openaiApiKey.trim() || undefined);
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

      <div className="form-divider" style={{ margin: '16px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>ADVANCED</div>

      <div className="input-group" style={{ marginBottom: 24 }}>
        <label className="input-label">OpenAI API Key (Optional)</label>
        <div style={{ position: 'relative' }}>
          <span className="url-input-icon">🔑</span>
          <input
            type="password"
            className="input-field"
            placeholder="sk-..."
            value={openaiApiKey}
            onChange={handleApiKeyChange}
            disabled={loading}
            style={{ paddingLeft: 40 }}
          />
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Bypass server rate limits by providing your own key. Saved locally.
        </p>
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
