import { IngestResponse, VideoSummary, SessionData } from '@/types';
import { getSession as getNextAuthSession } from 'next-auth/react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://vidcompare-backend.onrender.com';

async function getHeaders(customHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
  const session = await getNextAuthSession();
  const token = (session as any)?.accessToken;
  const headers: Record<string, string> = { ...customHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function createCheckoutSession(): Promise<{ url: string }> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/api/v1/stripe/create-checkout-session`, {
    method: 'POST',
    headers,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create checkout session');
  }

  return res.json();
}

/**
 * Kick off ingestion for two video URLs.
 * Returns session ID + initial video metadata.
 */
export async function ingestVideos(
  youtubeUrl: string,
  instagramUrl?: string,
  geminiApiKey?: string
): Promise<IngestResponse> {
  const session = await getNextAuthSession();
  const youtubeAccessToken = (session as any)?.youtubeAccessToken;

  const headers = await getHeaders({ 'Content-Type': 'application/json' });
  const payload: any = {
    youtube_url: youtubeUrl,
    youtube_access_token: youtubeAccessToken,
  };
  if (instagramUrl) payload.instagram_url = instagramUrl;
  if (geminiApiKey) payload.gemini_api_key = geminiApiKey;

  const res = await fetch(`${API_BASE}/api/v1/ingest`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Ingestion failed (${res.status})`);
  }

  return res.json();
}

/**
 * Stream chat responses via SSE using fetch + ReadableStream.
 * Calls onToken for each text chunk, onDone when the stream ends.
 */
export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onDone: (citations: any[]) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const openaiApiKey = typeof window !== 'undefined' ? localStorage.getItem('openai_api_key') : null;
    const headers = await getHeaders({ 'Content-Type': 'application/json' });
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        session_id: sessionId,
        message,
        openai_api_key: openaiApiKey || undefined,
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      onError(body.detail || `Chat failed (${res.status})`);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      onError('No response stream available');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let citations: any[] = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      // keep last incomplete line in buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const data = trimmed.slice(6);
        if (data === '[DONE]') {
          onDone(citations);
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.token) {
            onToken(parsed.token);
          }
          if (parsed.citations) {
            citations = parsed.citations;
          }
          // handle error events from the stream
          if (parsed.error) {
            onError(parsed.error);
            return;
          }
        } catch {
          // not JSON, treat as raw text token
          onToken(data);
        }
      }
    }

    // stream ended without [DONE] — still call onDone
    onDone(citations);
  } catch (err: any) {
    onError(err.message || 'Connection failed');
  }
}

/**
 * Fetch session data (video metadata + status).
 */
export async function getSession(sessionId: string): Promise<SessionData> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/api/v1/session/${sessionId}`, { headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to load session (${res.status})`);
  }

  return res.json();
}

/**
 * Fetch user sessions (requires auth)
 */
export async function getUserSessions() {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/api/v1/session/my-sessions`, { headers });
  
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to load user sessions (${res.status})`);
  }

  return res.json();
}

// -- Helpers --

export function formatNumber(n: number | null): string {
  if (n === null || n === undefined) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  return n.toLocaleString();
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
