export interface VideoSummary {
  title: string | null;
  creator: string | null;
  platform: string;
  views: number | null;
  likes: number | null;
  comments: number | null;
  duration_sec: number | null;
  engagement_rate: number | null;
  thumbnail_url: string | null;
  upload_date: string | null;
}

export interface IngestResponse {
  session_id: string;
  videos: {
    A: VideoSummary;
    B: VideoSummary;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface Citation {
  video: 'A' | 'B';
  chunk_id: string;
  text?: string;
}

export interface SessionData {
  session_id: string;
  videos: {
    A: VideoSummary;
    B: VideoSummary;
  };
  status: 'processing' | 'ready' | 'error';
  created_at?: string;
}

// Progress stepper
export type IngestionStep = 'fetching' | 'transcribing' | 'chunking' | 'ready';

export const INGESTION_STEPS: { key: IngestionStep; label: string }[] = [
  { key: 'fetching', label: 'Fetching metadata' },
  { key: 'transcribing', label: 'Transcribing' },
  { key: 'chunking', label: 'Analyzing' },
  { key: 'ready', label: 'Ready' },
];
