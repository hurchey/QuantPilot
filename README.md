# QuantPilot

A quant-focused full-stack SaaS app for uploading market data, defining trading strategies, running backtests, and reviewing risk/performance metrics.

## What You'll See

- **Home** — Overview and quick links to the main workflow (Create Account → Upload Data → Build Strategy → Run Backtest)
- **Market Data** — Import OHLCV data via demo datasets, CSV upload, Parquet upload, or symbol fetch from Yahoo Finance
- **Stock Profile** — Deep-dive into a single stock: current/previous price, 52-week and all-time highs/lows, volume, beta, P/E, and options Greeks (delta, gamma, theta, vega)
- **Strategies** — Define SMA crossover parameters and other strategy configurations
- **Backtests** — Run backtests and view results
- **Dashboard** — Equity curves, drawdown charts, trade tables, and metrics (PnL, Sharpe ratio, win rate, max drawdown)

## Tech Stack

- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, Recharts
- **API:** Expects a backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:3000`) with endpoints like `/quant/data`, `/quant/strategies`, `/quant/backtests`

## Getting Started

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Ensure the backend API is running if you want full functionality.
