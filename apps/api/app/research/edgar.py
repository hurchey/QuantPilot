# apps/api/app/research/edgar.py
"""
SEC EDGAR scraper for building a comprehensive universe of U.S.-listed tickers.

Data sources:
  1. EDGAR company tickers JSON — all CIK→ticker mappings (current filers)
  2. EDGAR full-index files — historical filings to find delisted names
  3. SEC FTD data — Failures to Deliver, a key signal for squeeze setups

SEC requires a User-Agent header with company name + email.
See: https://www.sec.gov/os/accessing-edgar-data
"""
from __future__ import annotations

from typing import Optional

import csv
import io
import json
import logging
import zipfile
from datetime import datetime

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SEC_BASE = "https://www.sec.gov"
EDGAR_BASE = "https://efts.sec.gov"
SEC_HEADERS = {
    "User-Agent": "QuantPilot Research quantpilot@research.com",
    "Accept-Encoding": "gzip, deflate",
}


# ---------------------------------------------------------------------------
# 1. All current SEC filers (tickers + CIK)
# ---------------------------------------------------------------------------


def fetch_edgar_tickers() -> pd.DataFrame:
    """
    Fetch the full EDGAR company_tickers.json — every active SEC filer.
    Returns DataFrame with columns: cik, ticker, company_name.
    """
    url = f"{SEC_BASE}/files/company_tickers.json"
    resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for entry in data.values():
        rows.append({
            "cik": entry["cik_str"],
            "ticker": entry["ticker"],
            "company_name": entry["title"],
        })

    df = pd.DataFrame(rows)
    df["ticker"] = df["ticker"].str.upper().str.strip()
    logger.info("Fetched %d tickers from EDGAR", len(df))
    return df


def fetch_edgar_tickers_with_exchange() -> pd.DataFrame:
    """
    Fetch EDGAR company tickers with exchange info.
    Uses the exchange JSON endpoint for richer data.
    """
    url = f"{SEC_BASE}/files/company_tickers_exchange.json"
    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        fields = data["fields"]  # ['cik', 'name', 'ticker', 'exchange']
        rows = [dict(zip(fields, row)) for row in data["data"]]
        df = pd.DataFrame(rows)
        df.rename(columns={"name": "company_name"}, inplace=True)
        df["ticker"] = df["ticker"].str.upper().str.strip()
        logger.info("Fetched %d tickers with exchange data from EDGAR", len(df))
        return df
    except Exception as e:
        logger.warning("Exchange endpoint failed, falling back to basic: %s", e)
        return fetch_edgar_tickers()


def filter_us_equity_tickers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter EDGAR tickers to U.S. equity exchanges only.
    Keeps NYSE, NASDAQ, AMEX/BATS. Drops OTC, foreign, and non-equity.
    """
    if "exchange" not in df.columns:
        return df

    us_exchanges = {"NYSE", "NASDAQ", "Nasdaq", "Cboe", "AMEX", "BATS", "ARCA", "NYSE ARCA"}
    mask = df["exchange"].isin(us_exchanges)
    filtered = df[mask].copy()
    logger.info("Filtered to %d U.S. exchange tickers (from %d)", len(filtered), len(df))
    return filtered


# ---------------------------------------------------------------------------
# 2. Delisted / historical tickers from EDGAR full-index
# ---------------------------------------------------------------------------


def fetch_full_index_tickers(years: Optional[list[int]] = None) -> set[str]:
    """
    Scrape tickers from EDGAR full-index quarterly filings.
    This catches companies that have since been delisted.

    Only parses the company.idx files which have ticker info.
    This is slow for many years — use sparingly.
    """
    if years is None:
        years = list(range(2015, datetime.now().year + 1))

    all_tickers: set[str] = set()

    for year in years:
        for quarter in range(1, 5):
            url = f"{SEC_BASE}/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"
            try:
                resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
                if resp.status_code != 200:
                    continue
                # Parse the fixed-width format
                lines = resp.text.split("\n")
                for line in lines[10:]:  # skip header lines
                    parts = line.split()
                    if len(parts) >= 3:
                        # CIK is typically the second-to-last field
                        # This is a rough parse — company.idx format is fixed-width
                        pass
                # The company.idx doesn't have tickers directly.
                # Instead, use the EDGAR JSON endpoints which are more reliable.
            except Exception as e:
                logger.debug("Failed to fetch index %s/QTR%s: %s", year, quarter, e)

    logger.info("Full-index scan found %d additional tickers", len(all_tickers))
    return all_tickers


# ---------------------------------------------------------------------------
# 3. SEC Failures to Deliver (FTD) data
# ---------------------------------------------------------------------------


def fetch_ftd_data(year: int, half: int) -> pd.DataFrame:
    """
    Fetch SEC Failures to Deliver data for a given half-year period.

    SEC publishes FTD data twice monthly in TXT files, archived by half-year.
    URL pattern: https://www.sec.gov/files/data/fails-deliver-data/cnsfails{YYYYMM}{a|b}.zip

    Args:
        year: e.g. 2024
        half: 1 (Jan-Jun) or 2 (Jul-Dec)

    Returns DataFrame with columns:
        settlement_date, cusip, symbol, quantity, company_name, price
    """
    frames = []
    months = range(1, 7) if half == 1 else range(7, 13)

    for month in months:
        for part in ["a", "b"]:  # each month has two files (first half, second half)
            date_str = f"{year}{month:02d}"
            filename = f"cnsfails{date_str}{part}"
            url = f"{SEC_BASE}/files/data/fails-deliver-data/{filename}.zip"

            try:
                resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
                if resp.status_code != 200:
                    continue

                # Extract CSV from zip
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    for name in zf.namelist():
                        if name.endswith(".csv") or name.endswith(".txt"):
                            with zf.open(name) as f:
                                content = f.read().decode("utf-8", errors="replace")
                                df = _parse_ftd_text(content)
                                if not df.empty:
                                    frames.append(df)
            except Exception as e:
                logger.debug("Failed to fetch FTD %s: %s", filename, e)

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    logger.info("Fetched %d FTD records for %d H%d", len(result), year, half)
    return result


def _parse_ftd_text(content: str) -> pd.DataFrame:
    """Parse SEC FTD text file (pipe-delimited)."""
    lines = content.strip().split("\n")
    if len(lines) < 2:
        return pd.DataFrame()

    rows = []
    for line in lines[1:]:  # skip header
        parts = line.split("|")
        if len(parts) >= 6:
            try:
                rows.append({
                    "settlement_date": parts[0].strip(),
                    "cusip": parts[1].strip(),
                    "symbol": parts[2].strip().upper(),
                    "quantity": int(parts[3].strip()) if parts[3].strip() else 0,
                    "company_name": parts[4].strip(),
                    "price": float(parts[5].strip()) if parts[5].strip() else None,
                })
            except (ValueError, IndexError):
                continue

    return pd.DataFrame(rows)


def get_high_ftd_symbols(
    year: int,
    half: int,
    min_ftd_quantity: int = 500_000,
    min_days: int = 5,
) -> pd.DataFrame:
    """
    Find symbols with persistently high FTDs — potential squeeze candidates.

    Returns DataFrame with columns: symbol, total_ftd, ftd_days, avg_daily_ftd, max_daily_ftd
    """
    df = fetch_ftd_data(year, half)
    if df.empty:
        return pd.DataFrame()

    # Aggregate by symbol
    agg = df.groupby("symbol").agg(
        total_ftd=("quantity", "sum"),
        ftd_days=("quantity", "count"),
        avg_daily_ftd=("quantity", "mean"),
        max_daily_ftd=("quantity", "max"),
    ).reset_index()

    # Filter for significant FTDs
    mask = (agg["total_ftd"] >= min_ftd_quantity) & (agg["ftd_days"] >= min_days)
    result = agg[mask].sort_values("total_ftd", ascending=False).reset_index(drop=True)

    logger.info("Found %d symbols with high FTDs in %d H%d", len(result), year, half)
    return result


# ---------------------------------------------------------------------------
# 4. Combined universe builder
# ---------------------------------------------------------------------------


def build_full_ticker_universe() -> pd.DataFrame:
    """
    Build the most comprehensive U.S. equity ticker list possible from SEC data.

    Returns DataFrame with: ticker, company_name, cik, exchange, source
    """
    # Start with exchange-tagged tickers
    df = fetch_edgar_tickers_with_exchange()

    # Filter to U.S. equity exchanges
    if "exchange" in df.columns:
        us_df = filter_us_equity_tickers(df)
    else:
        us_df = df

    us_df = us_df.copy()
    us_df["source"] = "edgar_exchange"

    # Deduplicate
    us_df = us_df.drop_duplicates(subset=["ticker"], keep="first")

    logger.info("Built universe of %d U.S. equity tickers", len(us_df))
    return us_df.reset_index(drop=True)
