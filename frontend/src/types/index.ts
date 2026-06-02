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
  follower_count: number | null;
  hashtags: string[] | null;
  is_cached?: boolean;
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
  suggested_questions?: string[];
}

export interface Citation {
  video_id: string;
  chunk_index: number;
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
