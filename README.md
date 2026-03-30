# QuantPilot

A quantitative research platform for studying extreme price dislocation events in equity markets. The core focus is building a structured, reproducible dataset of stocks that experienced 500%+ short-horizon moves -- identifying what drove them, classifying them by structural cause, and analyzing patterns across events.

## Research Focus: Extreme Dislocations

The central question: **What structural conditions produce 500%+ 3-day price moves, and can they be categorized and predicted?**

The platform implements a six-step research pipeline:

### 1. Universe Definition
Build a scan universe from multiple sources to avoid survivorship bias:
- **Seed list** -- 60+ curated known extreme movers (GME, AMC, SPRT, DWAC, SAVA, HKD, etc.) used to validate the scanner before running at scale
- **SEC EDGAR** -- Full historical universe including delisted tickers
- **High FTD symbols** -- Stocks with elevated failure-to-deliver rates, often precursors to squeeze dynamics
- **Alpha Vantage listing status** -- Active and historical listings with IPO/delist dates

### 2. Scanning
Systematic detection of extreme moves across the universe:
- Rolling 1-day and 3-day return computation over full price history
- Qualification threshold: 1-day OR 3-day return >= 500%
- Nearby event clustering (within 7 trading days) to avoid double-counting
- Minimum price filter to exclude sub-penny noise
- Dual labeling: Label A (100%+ best return), Label B (500%+ best return)

### 3. Data Collection
For each qualified event, capture the full context window:
- Price data: start price, peak price, 1-day and 3-day returns
- Volume profile: event-day volume, 20-day pre-event average, volume ratio
- Event timing: start date, peak date, end date

### 4. Enrichment
Layer on fundamental and structural data via yfinance:
- **Share structure** -- shares outstanding, float shares, market cap at event start
- **Short interest** -- shares short, short % of float, days to cover
- **Company identity** -- sector, industry, exchange, security type (common, ADR, SPAC, closed-end fund)
- **IPO context** -- IPO date, days since IPO at event time
- **Options context** -- options availability, pre-event implied volatility, call/put open interest

### 5. Classification
Assign each event to a structural taxonomy bucket with confidence scoring:
- **Short squeeze** -- High short %, elevated days to cover, volume spike
- **Biotech catalyst** -- Healthcare/pharma with FDA approval or trial data
- **SPAC/de-SPAC** -- Merger completion pops with tiny post-merger float
- **Penny stock pump** -- Sub-$5, low float, volume spike without fundamental catalyst
- **Technical breakout** -- Low float + gamma squeeze indicators
- **M&A** -- Merger/acquisition announcements
- **Earnings surprise** -- Extreme earnings beats
- **Sector momentum** -- Contagion from broader sector moves
- **Restructuring** -- Bankruptcy exit, reverse split, debt restructuring
- **Regulatory** -- Non-biotech regulatory catalysts
- **Unknown** -- Insufficient data to classify

### 6. Analysis and Export
- Dataset statistics: total events, label distribution, bucket distribution, top symbols, continuation rates
- Event-level detail views with all enrichment fields
- Export to JSON/CSV for external analysis and modeling

## Supporting Infrastructure

The research pipeline is supported by a broader quant platform that provides data ingestion, backtesting, and analytics:

### Market Data and Backtesting
- OHLCV data ingestion via CSV, Parquet, or yfinance fetch
- SMA crossover backtesting with realistic execution simulation (market impact, slippage, spread, fees)
- Equity curve tracking, drawdown analysis, trade-level PnL
- Volatility profiling and regime detection

### Options Analytics
- Live option chains (Market Data API, yfinance)
- Black-Scholes Greeks and implied volatility solver
- Risk-free rate management (SOFR, T-bills)

### Sentiment Analysis
- Multi-source aggregation: Alpha Vantage news, Finnhub, Stocktwits, Reddit
- NLP ensemble: VADER + optional FinBERT consensus scoring

## Data Sources

| Source | Role in Research |
|--------|-----------------|
| yfinance | Primary source for OHLCV history, fundamentals, float/short interest, options chains |
| Alpha Vantage | Stock universe listings (active + delisted), news sentiment |
| Finnhub | Company news, sentiment metrics |
| Market Data API | Options chains with reliable bid/ask spreads for IV context |
| SEC EDGAR | Full historical ticker universe for survivorship-bias-free scanning |
| Reddit (PRAW) | Social sentiment signals around event dates |
| Stocktwits | Retail trader sentiment |
| FRED | Risk-free rates for options pricing |

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Uvicorn |
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, Recharts |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Data Science** | pandas, numpy, pyarrow, py_vollib, vaderSentiment |

## Project Structure

```
apps/
  api/app/
    research/            # Core research pipeline
      scanner.py         #   Event detection (500%+ 3-day moves)
      enricher.py        #   Fundamental data enrichment
      taxonomy.py        #   Structural classification
      seed_list.py       #   Curated known extreme movers
      universe_builder.py#   Multi-source universe construction
      edgar.py           #   SEC EDGAR / FTD data
    quant/               # Backtesting and analytics modules
    routers/             # API endpoints
    services/            # External data integrations
    models.py            # SQLAlchemy models (DislocationEvent, DislocationFeature, MarketBar, etc.)
  web/src/
    app/research/        # Research UI (event browser, scanner, stats)
    app/                 # Other pages (backtests, stocks, options, dashboard)
    components/          # UI components, charts, tables
```

## Getting Started

### Backend

```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configure API keys: `ALPHAVANTAGE_API_KEY`, `FINNHUB_API_KEY`, `MARKETDATA_API_KEY`, and auth settings: `JWT_SECRET`, `DATABASE_URL`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to point at the backend (default `http://localhost:8000`).

## Key Research Endpoints

```
POST /quant/research/build-full        # Run complete pipeline (seeds + EDGAR + FTD + enrich + classify)
POST /quant/research/scan              # Scan specific symbols for dislocations
POST /quant/research/scan-universe     # Scan a predefined universe
POST /quant/research/build-seeds       # Build from curated seed list only
POST /quant/research/enrich            # Enrich existing events with fundamentals
POST /quant/research/classify          # Assign taxonomy buckets
GET  /quant/research/events            # Browse events with label/bucket filters
GET  /quant/research/events/{id}       # Event detail with all features
GET  /quant/research/stats             # Dataset statistics
GET  /quant/research/export            # Export as JSON/CSV
GET  /quant/research/seed-list         # View curated seed events
GET  /quant/research/ftd-signals       # High failure-to-deliver symbols
```
