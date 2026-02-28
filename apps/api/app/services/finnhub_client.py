"""
Finnhub API client: news, news sentiment.
https://finnhub.io/docs/api
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from app.config import settings

BASE_URL = "https://finnhub.io/api/v1"


def _get_token() -> str:
    if not settings.finnhub_api_key:
        raise ValueError("FINNHUB_API_KEY is not set")
    return settings.finnhub_api_key


def _request(path: str, params: dict[str, str] | None = None) -> dict[str, Any] | list[Any]:
    token = _get_token()
    url = f"{BASE_URL}{path}"
    p = params or {}
    p["token"] = token
    r = requests.get(url, params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def get_company_news(
    symbol: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    Company news for symbol. from_date/to_date: YYYY-MM-DD.
    """
    if not settings.finnhub_api_key:
        return []
    try:
        now = datetime.now(timezone.utc)
        to_d = to_date or now.strftime("%Y-%m-%d")
        from_d = from_date or (now - timedelta(days=7)).strftime("%Y-%m-%d")
        data = _request(
            "/company-news",
            {"symbol": symbol.strip().upper(), "from": from_d, "to": to_d},
        )
        return data if isinstance(data, list) else []
    except Exception:
        return []


def get_news_sentiment(symbol: str) -> dict[str, Any]:
    """
    News sentiment for symbol. Returns buzz, articlesInLastWeek, sentiment scores.
    """
    if not settings.finnhub_api_key:
        return {}
    try:
        data = _request("/news-sentiment", {"symbol": symbol.strip().upper()})
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def is_available() -> bool:
    return bool(settings.finnhub_api_key)
