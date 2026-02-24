"""Security utilities for input validation and query safety."""


def clamp_limit(raw_limit, default=25, min_limit=1, max_limit=100):
    """Clamp a user-provided limit to a safe range."""
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return default

    return max(min_limit, min(limit, max_limit))
