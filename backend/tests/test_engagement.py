from app.services.chunking import compute_engagement_rate


def test_normal_engagement():
    """Standard case with real numbers."""
    rate = compute_engagement_rate(views=10000, likes=500, comments=50)
    assert rate == 5.5  # (500 + 50) / 10000 * 100


def test_zero_views():
    """Zero views should return 0.0, not crash."""
    rate = compute_engagement_rate(views=0, likes=100, comments=10)
    assert rate == 0.0


def test_none_views():
    """None views should return 0.0."""
    rate = compute_engagement_rate(views=None, likes=100, comments=10)
    assert rate == 0.0


def test_none_likes_and_comments():
    """None likes/comments should be treated as 0."""
    rate = compute_engagement_rate(views=1000, likes=None, comments=None)
    assert rate == 0.0


def test_partial_none():
    """Only likes provided, comments is None."""
    rate = compute_engagement_rate(views=1000, likes=50, comments=None)
    assert rate == 5.0  # 50 / 1000 * 100


def test_high_engagement():
    """Viral-style engagement rate."""
    rate = compute_engagement_rate(views=100, likes=80, comments=30)
    assert rate == 110.0  # (80 + 30) / 100 * 100


def test_large_numbers():
    """Millions of views."""
    rate = compute_engagement_rate(views=10_000_000, likes=500_000, comments=50_000)
    expected = (500_000 + 50_000) / 10_000_000 * 100
    assert rate == round(expected, 4)
