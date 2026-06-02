import { VideoSummary } from '@/types';
import { formatNumber, formatDuration } from '@/lib/api';

interface VideoCardProps {
  video: VideoSummary;
  label: 'A' | 'B';
}

export default function VideoCard({ video, label }: VideoCardProps) {
  const engagementColor = (() => {
    if (!video.engagement_rate) return '';
    if (video.engagement_rate > 5) return 'engagement-good';
    if (video.engagement_rate > 2) return 'engagement-mid';
    return 'engagement-low';
  })();

  const platformClass = video.platform === 'youtube' ? 'platform-youtube' : 'platform-instagram';
  const platformLabel = video.platform === 'youtube' ? 'YouTube' : 'Instagram';

  return (
    <div className={`glass-card video-card animate-slide-up ${label === 'A' ? 'delay-1' : 'delay-2'}`}>
      <div className={`video-card-gradient-bar video-${label.toLowerCase()}`} />
      <div className="video-card-content">
        <div className={`video-card-label label-${label.toLowerCase()}`}>
          {label}
        </div>
        {video.is_cached && (
          <div className="video-card-label" style={{right: '1rem', left: 'auto', background: 'rgba(255, 193, 7, 0.2)', color: '#ffc107', border: '1px solid rgba(255, 193, 7, 0.4)'}}>
            Loaded from cache ⚡
          </div>
        )}

        {/* Thumbnail */}
        <div className="video-thumbnail-wrapper">
          {video.thumbnail_url ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={
                video.platform === 'instagram' 
                  ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/media/proxy-image?url=${encodeURIComponent(video.thumbnail_url)}`
                  : video.thumbnail_url
              }
              alt={video.title || 'Video thumbnail'}
              className="video-thumbnail"
              onError={(e) => {
                // Fallback to avoid broken image icons if proxy fails
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          ) : (
            <div className="video-thumbnail-placeholder">🎬</div>
          )}
          {video.duration_sec && (
            <span className="video-duration-badge">
              {formatDuration(video.duration_sec)}
            </span>
          )}
        </div>

        {/* Meta */}
        <span className={`video-platform-badge ${platformClass}`}>
          {platformLabel}
        </span>
        {video.upload_date && (
          <p className="video-upload-date">Uploaded {video.upload_date}</p>
        )}
        <h3 className="video-title">{video.title || 'Untitled Video'}</h3>
        <p className="video-creator">
          {video.creator || 'Unknown creator'}
          {video.follower_count && (
            <span className="follower-count"> · {formatNumber(video.follower_count)} followers</span>
          )}
        </p>

        {/* Metrics */}
        <div className="video-metrics">
          <div className="metric-item">
            <div className="metric-value">{formatNumber(video.views)}</div>
            <div className="metric-label">Views</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">{formatNumber(video.likes)}</div>
            <div className="metric-label">Likes</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">{formatNumber(video.comments)}</div>
            <div className="metric-label">Comments</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">{formatDuration(video.duration_sec)}</div>
            <div className="metric-label">Duration</div>
          </div>

          {/* Engagement Rate - spans full width */}
          <div className="metric-item engagement-rate">
            <div className="metric-label" style={{ marginBottom: 4 }}>Engagement Rate</div>
            <div className={`engagement-value ${engagementColor}`}>
              {video.engagement_rate !== null
                ? `${video.engagement_rate.toFixed(2)}%`
                : '—'}
            </div>
          </div>
        </div>

        {video.hashtags && video.hashtags.length > 0 && (
          <div className="video-hashtags">
            {video.hashtags.slice(0, 5).map((tag, i) => (
              <span key={i} className="hashtag-badge">#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
