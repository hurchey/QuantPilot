"""
Reddit API client (PRAW): fetch posts mentioning stock symbols.
https://www.reddit.com/dev/api/
Create app at https://www.reddit.com/prefs/apps (script type).
"""

from __future__ import annotations

from typing import Any

from app.config import settings


def _get_praw():
    try:
        import praw
    except ImportError:
        return None
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return None
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent or "QuantPilot/1.0",
    )


def search_symbol(
    symbol: str,
    subreddits: tuple[str, ...] = ("wallstreetbets", "stocks", "investing"),
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Search Reddit for posts mentioning symbol. Returns list of {title, body, score, created}.
    """
    reddit = _get_praw()
    if reddit is None:
        return []

    symbol = symbol.strip().upper()
    results: list[dict[str, Any]] = []

    try:
        for sub in subreddits:
            try:
                subreddit = reddit.subreddit(sub)
                # Search for symbol in title or selftext
                for post in subreddit.search(symbol, limit=min(limit // len(subreddits), 25), time_filter="week"):
                    text = f"{getattr(post, 'title', '')} {getattr(post, 'selftext', '')}"
                    if symbol in text.upper() or f"${symbol}" in text:
                        results.append({
                            "title": getattr(post, "title", ""),
                            "body": getattr(post, "selftext", ""),
                            "score": getattr(post, "score", 0),
                            "created_utc": getattr(post, "created_utc", 0),
                            "subreddit": sub,
                        })
            except Exception:
                continue
    except Exception:
        pass

    return results[:limit]


def is_available() -> bool:
    return bool(settings.reddit_client_id and settings.reddit_client_secret)
