"""
Sentiment ensemble: VADER + FinBERT + consensus logic.

Multiple NLP models check each other for robust sentiment scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnsembleResult:
    """Consensus sentiment result."""

    score: float  # -1 to 1
    confidence: float  # 0 to 1
    method_used: str  # "consensus" | "finbert" | "vader" | "fallback"
    scores: dict[str, float]  # vader, finbert, (llm)
    agreement: float  # 1 - (max - min), higher = more agreement
    flags: list[str]


def _vader_score(text: str) -> float | None:
    """VADER sentiment. Returns -1 to 1."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        compound = analyzer.polarity_scores(text).get("compound", 0)
        return max(-1.0, min(1.0, compound))
    except Exception:
        return None


def _finbert_score(text: str) -> float | None:
    """FinBERT sentiment. Returns -1 to 1."""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch

        model_name = "ProsusAI/finbert"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

        inputs = tokenizer(text[:512], return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        # positive, negative, neutral
        score = float(probs[0] - probs[1])  # positive - negative -> -1 to 1
        return max(-1.0, min(1.0, score))
    except Exception:
        return None


def run_ensemble(texts: list[str]) -> EnsembleResult:
    """
    Run VADER + FinBERT on texts, apply consensus logic.
    texts: list of text chunks (e.g. news headlines, social posts)
    """
    if not texts:
        return EnsembleResult(
            score=0.0,
            confidence=0.0,
            method_used="fallback",
            scores={},
            agreement=0.0,
            flags=["no_input"],
        )

    # Aggregate text for analysis (or analyze each and average)
    combined = " ".join(t[:200] for t in texts if t)[:2000]

    scores: dict[str, float] = {}
    vader = _vader_score(combined)
    if vader is not None:
        scores["vader"] = vader

    finbert = _finbert_score(combined)
    if finbert is not None:
        scores["finbert"] = finbert

    if not scores:
        return EnsembleResult(
            score=0.0,
            confidence=0.0,
            method_used="fallback",
            scores={},
            agreement=0.0,
            flags=["no_nlp_available"],
        )

    # Consensus logic
    vals = list(scores.values())
    agreement = 1.0 - (max(vals) - min(vals)) if len(vals) >= 2 else 1.0
    flags: list[str] = []

    if agreement >= 0.7:
        # High agreement: weighted average (FinBERT 0.6, VADER 0.4)
        w_fb = 0.6 if "finbert" in scores else 0.0
        w_v = 0.4 if "vader" in scores else 0.0
        total_w = w_fb + w_v
        if total_w > 0:
            score = (scores.get("finbert", 0) * w_fb + scores.get("vader", 0) * w_v) / total_w
        else:
            score = vals[0]
        method = "consensus"
        confidence = 0.9
        flags.append("high_agreement")
    elif agreement >= 0.4:
        # Medium: drop outlier if 2 models, else use FinBERT preferred
        if "finbert" in scores and "vader" in scores:
            diff_fb = abs(scores["finbert"] - (sum(vals) / len(vals)))
            diff_v = abs(scores["vader"] - (sum(vals) / len(vals)))
            outlier = "vader" if diff_v > diff_fb else "finbert"
            score = scores.get("finbert" if outlier == "vader" else "vader", vals[0])
        else:
            score = vals[0]
        method = "consensus"
        confidence = 0.6
        flags.append("medium_agreement")
    else:
        # Low agreement: trust FinBERT (finance domain) over VADER
        score = scores.get("finbert", scores.get("vader", vals[0]))
        method = "finbert" if "finbert" in scores else "vader"
        confidence = 0.4
        flags.append("low_agreement")

    return EnsembleResult(
        score=max(-1.0, min(1.0, score)),
        confidence=confidence,
        method_used=method,
        scores=scores,
        agreement=agreement,
        flags=flags,
    )
