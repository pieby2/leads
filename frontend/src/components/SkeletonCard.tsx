export default function SkeletonCard() {
  return (
    <div className="glass-card skeleton-card">
      <div className="skeleton skeleton-thumbnail" />
      <div className="skeleton skeleton-line skeleton-line-short" />
      <div className="skeleton skeleton-line skeleton-line-medium" />
      <div className="skeleton skeleton-line skeleton-line-short" style={{ marginBottom: 20 }} />
      <div className="skeleton-metrics-grid">
        <div className="skeleton skeleton-metric" />
        <div className="skeleton skeleton-metric" />
        <div className="skeleton skeleton-metric" />
        <div className="skeleton skeleton-metric" />
      </div>
    </div>
  );
}
