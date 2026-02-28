export type WorkflowPhaseId =
  | "pre-market"
  | "open"
  | "during-day"
  | "midday"
  | "close"
  | "post-market";

export type ChecklistItemDef = {
  id: string;
  label: string;
  whyItMatters: string;
  /** Optional link to app page (e.g. /dashboard, /backtests) */
  link?: string;
};

export type WorkflowPhaseDef = {
  id: WorkflowPhaseId;
  label: string;
  description: string;
  items: ChecklistItemDef[];
};

export const WORKFLOW_PHASES: WorkflowPhaseDef[] = [
  {
    id: "pre-market",
    label: "Pre-market",
    description: "Before the session starts. Set yourself up for a disciplined day.",
    items: [
      {
        id: "pm-1",
        label: "Check strategy health (PnL, drawdowns, fills, slippage)",
        whyItMatters:
          "Before risking capital, verify your strategies are behaving as expected. Unexpected drawdowns or strange fills can signal a bug or regime change.",
        link: "/dashboard",
      },
      {
        id: "pm-2",
        label: "Validate market data (stale quotes, missing symbols, outliers)",
        whyItMatters:
          "Bad data leads to bad decisions. A single stale price can trigger incorrect signals or risk miscalculations.",
        link: "/data",
      },
      {
        id: "pm-3",
        label: "Confirm connectivity (broker, exchange, API status)",
        whyItMatters:
          "If your order gateway is down or throttled, you might not get fills when you need them—or worse, miss a stop.",
      },
      {
        id: "pm-4",
        label: "Review positions & exposures (gross/net, sector, beta)",
        whyItMatters:
          "Know what you're holding before the bell. Unintended exposure can turn a good day into a disaster.",
      },
      {
        id: "pm-5",
        label: "Run pre-trade risk checks (max size, participation, kill-switch)",
        whyItMatters:
          "Risk limits exist for a reason. A single oversized order or runaway algo can wipe out weeks of gains.",
      },
      {
        id: "pm-6",
        label: "Update market state inputs (rates, vol, events)",
        whyItMatters:
          "Rates, volatility, and scheduled events (earnings, dividends) affect how your models should behave. Update these before trading.",
      },
      {
        id: "pm-7",
        label: "Plan session settings (risk budget, aggressiveness, what to avoid)",
        whyItMatters:
          "Decide in advance how much risk you're willing to take and how aggressive execution should be. Avoid ad-hoc decisions under pressure.",
      },
      {
        id: "pm-8",
        label: "Sync with research/engineering (config changes, deploys, experiments)",
        whyItMatters:
          "Know what changed overnight. A new parameter or experiment could explain unexpected behavior.",
      },
    ],
  },
  {
    id: "open",
    label: "Open / Early Session",
    description: "First 30–60 minutes. The open is noisy—stay vigilant.",
    items: [
      {
        id: "open-1",
        label: "Tight live supervision (auctions, wide spreads)",
        whyItMatters:
          "The open is noisy. Orders can behave differently in auctions and when spreads are wide. Watch closely.",
      },
      {
        id: "open-2",
        label: "Watch microstructure (halts, crossed markets, abnormal spreads)",
        whyItMatters:
          "Halts, crossed markets, and liquidity vacuums can cause bad fills or missed trades. Stay alert.",
      },
      {
        id: "open-3",
        label: "Control aggressiveness (throttle, widen/narrow, reduce size)",
        whyItMatters:
          "If conditions are outside your model's assumptions, dial back. Better to miss a trade than take a bad one.",
      },
      {
        id: "open-4",
        label: "Confirm hedging works (inventory doesn't drift)",
        whyItMatters:
          "If you're hedged, verify the hedge is holding. Unintended directional exposure can blow up quickly.",
      },
    ],
  },
  {
    id: "during-day",
    label: "During the Day",
    description: "The live ops loop. Monitor, tune, and respond.",
    items: [
      {
        id: "day-1",
        label: "Monitor PnL attribution (signal, product, venue, time)",
        whyItMatters:
          "Know what's driving performance. Is it one signal, one product, or one venue? Understanding this helps you tune.",
      },
      {
        id: "day-2",
        label: "Track execution quality (slippage, fill probability, queue position)",
        whyItMatters:
          "Execution costs eat into alpha. Monitor slippage vs expectation and fill rates to spot problems early.",
      },
      {
        id: "day-3",
        label: "Tune execution knobs (order types, participation, cancel/replace)",
        whyItMatters:
          "Small tweaks to order types, participation rate, or cancel cadence can improve fills without changing the signal.",
      },
      {
        id: "day-4",
        label: "Handle anomalies fast (drawdown, strange fills, rejects)",
        whyItMatters:
          "When something goes wrong, decide quickly: fix, hedge, or stop. Indecision costs money.",
      },
      {
        id: "day-5",
        label: "Enforce risk limits (exposures, leverage, VaR)",
        whyItMatters:
          "When thresholds are hit, cut risk. No exceptions.",
      },
      {
        id: "day-6",
        label: "Coordinate incident response (data bugs, latency, infra)",
        whyItMatters:
          "Data feed bugs and infra failures need fast coordination. Know who to call and what to do.",
      },
      {
        id: "day-7",
        label: "Keep runbook notes (what happened, what you changed, why)",
        whyItMatters:
          "Document incidents and changes. You'll need this for compliance, debugging, and learning.",
      },
    ],
  },
  {
    id: "midday",
    label: "Midday",
    description: "Improvement and diagnostics. Use the lull to tune and clean.",
    items: [
      {
        id: "mid-1",
        label: "Run quick diagnostics (replay data, isolate losses)",
        whyItMatters:
          "Was today's loss from the signal, execution, or data? Replaying data helps isolate the cause.",
        link: "/backtests",
      },
      {
        id: "mid-2",
        label: "Test small improvements safely (params, filters, throttling)",
        whyItMatters:
          "Make one change at a time. Test in paper or small size before scaling.",
      },
      {
        id: "mid-3",
        label: "Clean up data problems (symbol mapping, corporate actions)",
        whyItMatters:
          "Bad data contaminates research. Fix symbol mapping and corporate action adjustments before they propagate.",
        link: "/data",
      },
      {
        id: "mid-4",
        label: "Review inventory rules (mean-reversion, when to hedge)",
        whyItMatters:
          "How fast does your inventory mean-revert? When do you hedge? Revisit these rules periodically.",
      },
    ],
  },
  {
    id: "close",
    label: "Close",
    description: "End of session. De-risk and reconcile.",
    items: [
      {
        id: "close-1",
        label: "De-risk if required (flatten or rebalance)",
        whyItMatters:
          "Some strategies hold overnight; others don't. Know your rules and execute them.",
      },
      {
        id: "close-2",
        label: "Position reconciliation (internal vs broker/exchange)",
        whyItMatters:
          "Your positions must match the broker. Resolve breaks immediately—they can hide bigger problems.",
      },
      {
        id: "close-3",
        label: "Trade reconciliation (busts, adjustments, missing fills)",
        whyItMatters:
          "Investigate busts, adjustments, and missing fills. Out-of-sequence messages can cause position errors.",
      },
    ],
  },
  {
    id: "post-market",
    label: "Post-market",
    description: "Deep dive and feedback. Learn from the day and feed into tomorrow.",
    items: [
      {
        id: "post-1",
        label: "Post-trade analysis (best/worst trades, failure patterns)",
        whyItMatters:
          "Identify what worked and what didn't. Consistent failure patterns point to fixable issues.",
        link: "/dashboard",
      },
      {
        id: "post-2",
        label: "Transaction cost analysis (spread, impact, timing, venue)",
        whyItMatters:
          "TCA reveals where you're leaving money on the table. Spread paid, market impact, and venue choice matter.",
      },
      {
        id: "post-3",
        label: "Signal health review (decay, crowding, drift, regime change)",
        whyItMatters:
          "Signals decay. Crowding and regime changes can kill alpha. Monitor feature distributions and performance by regime.",
      },
      {
        id: "post-4",
        label: "Stress & scenario review (what if vol doubles, liquidity disappears)",
        whyItMatters:
          "Stress test your portfolio. Know how it behaves when vol spikes or correlations break.",
      },
      {
        id: "post-5",
        label: "Daily recap (what happened, issues, actions, proposed changes)",
        whyItMatters:
          "Summarize the day: issues, actions taken, and what to change tomorrow. This feeds into the next pre-market.",
      },
    ],
  },
];

/** Ongoing weekly/monthly work — where a lot of value is created */
export type OngoingWorkflowId =
  | "ongoing-1"
  | "ongoing-2"
  | "ongoing-3"
  | "ongoing-4"
  | "ongoing-5";

export const ONGOING_WORKFLOW_ITEMS: (ChecklistItemDef & { id: OngoingWorkflowId })[] = [
  {
    id: "ongoing-1",
    label: "Research new edges (signals, features, alternative data, microstructure)",
    whyItMatters:
      "Alpha decays. New signals, features, and data sources keep your edge fresh. Microstructure effects and alternative data can uncover opportunities others miss.",
    link: "/strategies",
  },
  {
    id: "ongoing-2",
    label: "Backtest & validate (out-of-sample, regime coverage, overfitting controls)",
    whyItMatters:
      "Never deploy without rigorous backtesting. Out-of-sample tests, regime coverage, and overfitting controls separate real alpha from curve-fitting.",
    link: "/backtests",
  },
  {
    id: "ongoing-3",
    label: "Improve production systems (monitoring, alerting, safer deploys, data pipelines)",
    whyItMatters:
      "Reliable infrastructure is table stakes. Better monitoring, alerting, and deploy pipelines reduce downtime and catch bugs before they cost money.",
  },
  {
    id: "ongoing-4",
    label: "Govern parameters & changes (approvals, experiment tracking, rollback criteria)",
    whyItMatters:
      "Who can change what? Clear approval flows, experiment tracking, and rollback criteria prevent accidental damage and make debugging easier.",
  },
  {
    id: "ongoing-5",
    label: "Cross-team collaboration (traders ↔ researchers ↔ engineers ↔ risk)",
    whyItMatters:
      "Quant trading is a team sport. Traders, researchers, engineers, and risk need to align on performance, stability, and priorities.",
  },
];

/** Quant trading lane — different styles, different emphasis */
export type QuantLaneId = "hft" | "options" | "systematic" | "semi-systematic";

export type QuantLaneDef = {
  id: QuantLaneId;
  label: string;
  shortLabel: string;
  description: string;
  emphasis: string[];
};

export const QUANT_LANES: QuantLaneDef[] = [
  {
    id: "hft",
    label: "HFT / Market Making",
    shortLabel: "HFT",
    description: "Real-time monitoring and microstructure tuning. Speed and latency matter a lot.",
    emphasis: ["Pre-market connectivity", "Open/early session supervision", "Microstructure", "Execution quality"],
  },
  {
    id: "options",
    label: "Options Market Making",
    shortLabel: "Options",
    description: "Constant inventory and Greeks management. Heavy hedging and volatility/surface awareness.",
    emphasis: ["Positions & exposures", "Greeks (delta, gamma, vega)", "Hedging", "Vol surface"],
  },
  {
    id: "systematic",
    label: "Systematic Hedge Fund",
    shortLabel: "Systematic",
    description: "Slower horizon. More time on research and portfolio construction; less intraday knob-turning.",
    emphasis: ["Research & backtesting", "Portfolio construction", "Signal health", "Regime coverage"],
  },
  {
    id: "semi-systematic",
    label: "Semi-Systematic",
    shortLabel: "Semi-Systematic",
    description: "Quantitative with discretionary overrides around events and risk conditions.",
    emphasis: ["Market state inputs", "Session settings", "Event-aware overrides", "Risk conditions"],
  },
];

export type MarketStateInputs = {
  keyRates?: string;
  volEnvironment?: "low" | "normal" | "elevated" | "crisis";
  keyEventsToday?: string;
  notes?: string;
};

export type SessionSettings = {
  riskBudgetPct?: number;
  executionAggressiveness?: "low" | "medium" | "high";
  avoidAroundEvents?: string;
  notes?: string;
};

export type WorkflowState = {
  date: string;
  phases: Record<WorkflowPhaseId, { items: { id: string; checked: boolean }[] }>;
  ongoing?: { items: { id: OngoingWorkflowId; checked: boolean }[] };
  selectedLane?: QuantLaneId;
  marketState?: MarketStateInputs;
  sessionSettings?: SessionSettings;
  lastUpdated: string;
};

const STORAGE_KEY = "quantpilot-workflow";

function getDateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function buildEmptyState(dateStr: string): WorkflowState {
  const phases: WorkflowState["phases"] = {} as WorkflowState["phases"];
  for (const phase of WORKFLOW_PHASES) {
    phases[phase.id] = {
      items: phase.items.map((item) => ({ id: item.id, checked: false })),
    };
  }
  const ongoing = {
    items: ONGOING_WORKFLOW_ITEMS.map((item) => ({ id: item.id, checked: false })),
  };
  return {
    date: dateStr,
    phases,
    ongoing,
    lastUpdated: new Date().toISOString(),
  };
}

export function loadWorkflowState(date: Date): WorkflowState {
  const dateStr = getDateKey(date);
  try {
    const raw = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (!raw) return buildEmptyState(dateStr);
    const parsed = JSON.parse(raw) as Record<string, WorkflowState>;
    const state = parsed[dateStr];
    if (!state) return buildEmptyState(dateStr);
    // Merge with current phase definitions in case items changed
    const merged = buildEmptyState(dateStr);
    for (const phase of WORKFLOW_PHASES) {
      const saved = state.phases?.[phase.id];
      if (saved?.items) {
        for (const savedItem of saved.items) {
          const idx = merged.phases[phase.id].items.findIndex((i) => i.id === savedItem.id);
          if (idx >= 0) merged.phases[phase.id].items[idx].checked = savedItem.checked;
        }
      }
    }
    merged.marketState = state.marketState;
    merged.sessionSettings = state.sessionSettings;
    merged.selectedLane = state.selectedLane;
    if (state.ongoing?.items) {
      merged.ongoing = { items: merged.ongoing!.items.map((m) => {
        const s = state.ongoing!.items.find((i) => i.id === m.id);
        return s ? { ...m, checked: s.checked } : m;
      }) };
    }
    merged.lastUpdated = state.lastUpdated ?? merged.lastUpdated;
    return merged;
  } catch {
    return buildEmptyState(dateStr);
  }
}

export function saveWorkflowState(state: WorkflowState): void {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed: Record<string, WorkflowState> = raw ? JSON.parse(raw) : {};
    parsed[state.date] = { ...state, lastUpdated: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    // ignore
  }
}
