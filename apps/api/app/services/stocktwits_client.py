"""
Stocktwits API client: stream/messages for symbol.
https://api.stocktwits.com/developers/docs
Public API - no auth needed for basic stream.
"""

from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://api.stocktwits.com/api/2"


def get_stream(symbol: str, limit: int = 30) -> list[dict[str, Any]]:
    """
    Fetch stream of messages for symbol. No auth required for basic use.
    Returns list of message dicts with body, sentiment, etc.
    """
    try:
        r = requests.get(
            f"{BASE_URL}/streams/symbol/{symbol.strip().upper()}.json",
            params={"limit": min(limit, 30)},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        messages = data.get("messages", [])
        return messages if isinstance(messages, list) else []
    except Exception:
        return []


def get_trending() -> list[dict[str, Any]]:
    """Trending symbols (optional)."""
    try:
        r = requests.get(f"{BASE_URL}/trending/symbols.json", timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("symbols", []) or []
    except Exception:
        return []
