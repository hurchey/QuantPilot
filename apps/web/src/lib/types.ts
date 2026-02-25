// apps/web/src/lib/types.ts

export type User = {
    id: number;
    email: string;
    created_at?: string;
    updated_at?: string;
  };
  
  export type Workspace = {
    id: number;
    name: string;
    user_id?: number;
    created_at?: string;
    updated_at?: string;
  };
  
  export type MeResponse = {
    user: User;
    workspace: Workspace | null;
  };
  
  export type AuthResponse = {
    message: string;
    user: User;
  };
  
  export type MessageResponse = {
    message: string;
  };
  
  export type Strategy = {
    id: number;
    workspace_id?: number;
    name: string;
    strategy_type: string;
    symbol: string;
    timeframe: string;
    parameters_json: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
  };
  
  export type SymbolTimeframe = {
    symbol: string;
    timeframe: string;
  };
  
  export type MarketBar = {
    id: number;
    workspace_id?: number;
    symbol: string;
    timeframe: string;
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  };
  
  export type UploadDataResponse = {
    message: string;
    symbol: string;
    timeframe: string;
    rows_received: number;
    rows_inserted: number;
    rows_skipped_duplicates: number;
  };
  
  export type BacktestRun = {
    id: number;
    workspace_id?: number;
    strategy_id: number;
    start_date: string;
    end_date: string;
    initial_capital: number;
    fees_bps: number;
    slippage_bps: number;
    status: string;
    metrics_json: Record<string, unknown>;
    created_at?: string;
    completed_at?: string | null;
  };
  
  export type BacktestRunCreateResponse = {
    message: string;
    run: BacktestRun;
    meta?: Record<string, unknown>;
  };
  
  export type BacktestDetailResponse = {
    run: BacktestRun;
    strategy?: Strategy | null;
  };
  
  export type Trade = {
    id: number;
    backtest_run_id: number;
    symbol: string;
    side: string;
    qty: number;
    price: number;
    timestamp: string;
    fee: number;
    realized_pnl?: number | null;
  };
  
  export type EquityPoint = {
    id: number;
    backtest_run_id: number;
    timestamp: string;
    equity: number;
    drawdown: number;
  };
  
  export type DashboardSummary = Record<string, unknown>;
  export type DashboardRisk = Record<string, unknown>;
  export type DashboardPerformance = Record<string, unknown>;