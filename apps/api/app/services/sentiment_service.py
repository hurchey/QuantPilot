"""
Sentiment / buzz score: ensemble NLP + multi-source aggregation.

Sources: Alpha Vantage, Finnhub, Stocktwits, Reddit
NLP: VADER + FinBERT (optional) with consensus logic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import alphavantage as av
from . import finnhub_client as fh
from . import reddit_client as rd
from . import stocktwits_client as st

# Lazy import to avoid loading heavy deps at startup
_ensemble = None


def _get_ensemble():
    global _ensemble
    if _ensemble is None:
        from ..quant.sentiment_ensemble import run_ensemble
        _ensemble = run_ensemble
    return _ensemble


@dataclass(slots=True)
class SentimentScore:
    """Composite sentiment/buzz score for a symbol."""

    symbol: str
    composite_score: float  # 0-100
    news_count: int
    social_count: int
    ensemble_sentiment: float  # -1 to 1 from NLP
    ensemble_confidence: float
    sources: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        f = float(val)
        return f if -10 <= f <= 10 else default
    except (TypeError, ValueError):
        return default


def _collect_texts_and_sentiments(symbol: str, limit_per_source: int = 30) -> tuple[list[str], list[float], list[str]]:
    """
    Fetch from all sources, return (texts, api_sentiments, sources_used).
    """
    texts: list[str] = []
    api_sentiments: list[float] = []
    sources_used: list[str] = []

    symbol = symbol.strip().upper()

    # 1. Alpha Vantage news
    try:
        feed = av.get_news_sentiment(tickers=symbol, limit=limit_per_source)
        for item in feed:
            title = item.get("title") or ""
            summary = item.get("summary") or ""
            texts.append(f"{title} {summary}")
            for ts in item.get("ticker_sentiment", []) or []:
                if (ts.get("ticker") or "").strip().upper() == symbol:
                    s = _safe_float(ts.get("ticker_sentiment_score"))
                    api_sentiments.append(s)
                    break
        if feed:
            sources_used.append("alphavantage")
    except Exception:
        pass

    # 2. Finnhub news + sentiment
    try:
        if fh.is_available():
            news = fh.get_company_news(symbol)
            for n in news[:limit_per_source]:
                texts.append(f"{n.get('headline', '')} {n.get('summary', '')}")
            sent = fh.get_news_sentiment(symbol)
            if sent:
                s = sent.get("sentiment") or sent.get("Sentiment") or {}
                if isinstance(s, dict):
                    bull = _safe_float(s.get("bullishPercent", s.get("BullishPercent")), 33)
                    bear = _safe_float(s.get("bearishPercent", s.get("BearishPercent")), 33)
                    # Map to -1..1: (bull - bear) / 100
                    api_sentiments.append(max(-1.0, min(1.0, (bull - bear) / 100.0)))
            if news or sent:
                sources_used.append("finnhub")
    except Exception:
        pass

    # 3. Stocktwits
    try:
        messages = st.get_stream(symbol, limit=limit_per_source)
        for m in messages:
            body = m.get("body") or ""
            if body:
                texts.append(body)
                # Stocktwits has sentiment: Bullish/Bearish
                sent_label = (m.get("entities", {}) or {}).get("sentiment", {})
                if isinstance(sent_label, dict):
                    label = (sent_label.get("basic") or "").lower()
                else:
                    label = str(sent_label).lower()
                if "bull" in label:
                    api_sentiments.append(0.5)
                elif "bear" in label:
                    api_sentiments.append(-0.5)
        if messages:
            sources_used.append("stocktwits")
    except Exception:
        pass

    # 4. Reddit
    try:
        if rd.is_available():
            posts = rd.search_symbol(symbol, limit=limit_per_source)
            for p in posts:
                texts.append(f"{p.get('title', '')} {p.get('body', '')}")
            if posts:
                sources_used.append("reddit")
    except Exception:
        pass

    return (texts, api_sentiments, sources_used)


def get_sentiment_score(
    symbol: str,
    limit_per_source: int = 30,
    use_ensemble: bool = True,
) -> SentimentScore:
    """
    Multi-source sentiment with ensemble NLP consensus.

    - Fetches from Alpha Vantage, Finnhub, Stocktwits, Reddit
    - Runs VADER + FinBERT (if installed) with consensus
    - Blends API sentiment + NLP ensemble into 0-100 score
    """
    symbol = symbol.strip().upper()
    texts, api_sentiments, sources_used = _collect_texts_and_sentiments(symbol, limit_per_source)

    news_count = len([t for t in texts if t])  # approximate
    social_count = sum(1 for s in sources_used if s in ("stocktwits", "reddit"))

    # Run NLP ensemble on collected text
    if use_ensemble and texts:
        run_ensemble_fn = _get_ensemble()
        result = run_ensemble_fn(texts)
        ensemble_sent = result.score
        ensemble_conf = result.confidence
    else:
        ensemble_sent = 0.0
        ensemble_conf = 0.0

    # Blend: API sentiment (if any) + ensemble
    if api_sentiments:
        api_avg = sum(api_sentiments) / len(api_sentiments)
        # Weight: 0.4 API + 0.6 ensemble when both; else use what we have
        if use_ensemble and texts:
            blended = 0.4 * api_avg + 0.6 * ensemble_sent
        else:
            blended = api_avg
    else:
        blended = ensemble_sent

    # Map -1..1 to 0..100
    composite = 50.0 + (blended * 50.0)
    composite = max(0.0, min(100.0, composite))

    # Buzz boost: more sources = slight boost (cap)
    if len(sources_used) >= 3:
        composite = min(100.0, composite * 1.05)

    return SentimentScore(
        symbol=symbol,
        composite_score=round(composite, 2),
        news_count=news_count,
        social_count=social_count,
        ensemble_sentiment=round(ensemble_sent, 4),
        ensemble_confidence=round(ensemble_conf, 4),
        sources=sources_used,
        raw_data={
            "texts_count": len(texts),
            "api_sentiments_count": len(api_sentiments),
            "sources": sources_used,
        },
    )
