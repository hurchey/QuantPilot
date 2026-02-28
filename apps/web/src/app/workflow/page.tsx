"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  WORKFLOW_PHASES,
  ONGOING_WORKFLOW_ITEMS,
  QUANT_LANES,
  type WorkflowPhaseId,
  type QuantLaneId,
  type MarketStateInputs,
  type SessionSettings,
} from "@/lib/workflow-data";
import { useWorkflowState } from "@/hooks/useWorkflowState";

function formatDate(d: Date): string {
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function WorkflowPhaseSection({
  phase,
  checkedItems,
  onToggle,
  isExpanded,
  onToggleExpand,
}: {
  phase: (typeof WORKFLOW_PHASES)[number];
  checkedItems: Set<string>;
  onToggle: (phaseId: WorkflowPhaseId, itemId: string) => void;
  isExpanded: boolean;
  onToggleExpand: () => void;
}) {
  const total = phase.items.length;
  const done = phase.items.filter((i) => checkedItems.has(i.id) || false).length;

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      <button
        type="button"
        onClick={onToggleExpand}
        className="w-full flex items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-800/50 transition-colors"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span
            className={`text-xs text-slate-500 shrink-0 transition-transform ${isExpanded ? "rotate-90" : ""}`}
            aria-hidden
          >
            ▶
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-slate-100">{phase.label}</h2>
            <p className="text-sm text-slate-400">{phase.description}</p>
          </div>
        </div>
        <span className="text-sm text-slate-500 shrink-0">
          {done}/{total}
        </span>
      </button>

      {isExpanded && (
        <div className="border-t border-slate-800 px-4 py-3 space-y-3">
          {phase.items.map((item) => (
            <ChecklistItemRow
              key={item.id}
              item={item}
              checked={checkedItems.has(item.id)}
              onToggle={() => onToggle(phase.id, item.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function ChecklistItemRow({
  item,
  checked,
  onToggle,
}: {
  item: { id: string; label: string; whyItMatters: string; link?: string };
  checked: boolean;
  onToggle: () => void;
}) {
  const [showWhy, setShowWhy] = useState(false);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
      <div className="flex gap-3">
        <div className="flex-shrink-0 pt-0.5">
          <input
            type="checkbox"
            id={item.id}
            checked={checked}
            onChange={onToggle}
            className="h-4 w-4 min-w-[1rem] rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500/50 focus:ring-2"
            aria-describedby={`${item.id}-why`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <label
            htmlFor={item.id}
            className="text-base font-medium text-slate-100 cursor-pointer block leading-snug"
          >
            {item.label}
          </label>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setShowWhy((s) => !s)}
              className="text-xs text-slate-500 hover:text-slate-400 transition-colors"
            >
              {showWhy ? "Hide" : "Why it matters"}
            </button>
            {item.link && (
              <>
                <span className="text-slate-600">·</span>
                <Link
                  href={item.link}
                  className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Open in app →
                </Link>
              </>
            )}
          </div>
          {showWhy && (
            <p
              id={`${item.id}-why`}
              className="mt-2 text-sm text-slate-400 italic leading-relaxed"
            >
              {item.whyItMatters}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function LaneSelector({
  selected,
  onSelect,
}: {
  selected: string | undefined;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-slate-200">Your trading style</h3>
      <p className="text-xs text-slate-500">
        Different quant styles emphasize different parts of the workflow.
      </p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {QUANT_LANES.map((lane) => (
          <button
            key={lane.id}
            type="button"
            onClick={() => onSelect(lane.id)}
            className={`rounded-lg border px-3 py-2.5 text-left text-sm transition-colors ${
              selected === lane.id
                ? "border-blue-500/60 bg-blue-500/10 text-slate-100"
                : "border-slate-700 bg-slate-800/60 text-slate-300 hover:border-slate-600 hover:bg-slate-800/80"
            }`}
          >
            <span className="font-medium">{lane.shortLabel}</span>
            <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">{lane.description}</p>
          </button>
        ))}
      </div>
      {selected && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/40 px-3 py-2 text-xs text-slate-400">
          <strong className="text-slate-300">Emphasis:</strong>{" "}
          {QUANT_LANES.find((l) => l.id === selected)?.emphasis.join(", ")}
        </div>
      )}
    </div>
  );
}

function MarketStateForm({
  value,
  onChange,
}: {
  value: MarketStateInputs | undefined;
  onChange: (v: MarketStateInputs) => void;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-200">Market state</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="keyRates" className="block text-xs text-slate-500 mb-1">
            Key rates
          </label>
          <input
            id="keyRates"
            type="text"
            placeholder="e.g. Fed funds 5.25%, SOFR 5.30%"
            value={value?.keyRates ?? ""}
            onChange={(e) => onChange({ ...value, keyRates: e.target.value })}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
        </div>
        <div>
          <label htmlFor="volEnv" className="block text-xs text-slate-500 mb-1">
            Vol environment
          </label>
          <select
            id="volEnv"
            value={value?.volEnvironment ?? ""}
            onChange={(e) =>
              onChange({
                ...value,
                volEnvironment: (e.target.value || undefined) as MarketStateInputs["volEnvironment"],
              })
            }
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100"
          >
            <option value="">Select...</option>
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="elevated">Elevated</option>
            <option value="crisis">Crisis</option>
          </select>
        </div>
      </div>
      <div>
        <label htmlFor="keyEvents" className="block text-xs text-slate-500 mb-1">
          Key events today
        </label>
        <input
          id="keyEvents"
          type="text"
          placeholder="e.g. AAPL earnings 4pm, FOMC 2pm"
          value={value?.keyEventsToday ?? ""}
          onChange={(e) => onChange({ ...value, keyEventsToday: e.target.value })}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
        />
      </div>
      <div>
        <label htmlFor="marketNotes" className="block text-xs text-slate-500 mb-1">
          Notes
        </label>
        <textarea
          id="marketNotes"
          rows={2}
          placeholder="Free-form notes..."
          value={value?.notes ?? ""}
          onChange={(e) => onChange({ ...value, notes: e.target.value })}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 resize-none"
        />
      </div>
    </div>
  );
}

function SessionSettingsForm({
  value,
  onChange,
}: {
  value: SessionSettings | undefined;
  onChange: (v: SessionSettings) => void;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-200">Session settings</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="riskBudget" className="block text-xs text-slate-500 mb-1">
            Risk budget (%)
          </label>
          <input
            id="riskBudget"
            type="number"
            min={0}
            max={100}
            step={0.5}
            placeholder="e.g. 2"
            value={value?.riskBudgetPct ?? ""}
            onChange={(e) => {
              const v = e.target.value ? Number(e.target.value) : undefined;
              onChange({ ...value, riskBudgetPct: v });
            }}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
        </div>
        <div>
          <label htmlFor="aggressiveness" className="block text-xs text-slate-500 mb-1">
            Execution aggressiveness
          </label>
          <select
            id="aggressiveness"
            value={value?.executionAggressiveness ?? ""}
            onChange={(e) =>
              onChange({
                ...value,
                executionAggressiveness: (e.target.value || undefined) as SessionSettings["executionAggressiveness"],
              })
            }
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100"
          >
            <option value="">Select...</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>
      <div>
        <label htmlFor="avoidEvents" className="block text-xs text-slate-500 mb-1">
          Avoid around events
        </label>
        <input
          id="avoidEvents"
          type="text"
          placeholder="e.g. No new positions 30min before FOMC"
          value={value?.avoidAroundEvents ?? ""}
          onChange={(e) => onChange({ ...value, avoidAroundEvents: e.target.value })}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
        />
      </div>
      <div>
        <label htmlFor="sessionNotes" className="block text-xs text-slate-500 mb-1">
          Notes
        </label>
        <textarea
          id="sessionNotes"
          rows={2}
          placeholder="Free-form notes..."
          value={value?.notes ?? ""}
          onChange={(e) => onChange({ ...value, notes: e.target.value })}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 resize-none"
        />
      </div>
    </div>
  );
}

export default function WorkflowPage() {
  const today = useMemo(() => new Date(), []);
  const {
    state,
    toggleItem,
    toggleOngoingItem,
    setMarketState,
    setSessionSettings,
    setSelectedLane,
  } = useWorkflowState(today);

  const [expandedPhases, setExpandedPhases] = useState<Set<WorkflowPhaseId>>(
    new Set(["pre-market"])
  );

  const checkedItemsByPhase = useMemo(() => {
    const map = new Map<WorkflowPhaseId, Set<string>>();
    if (!state) return map;
    for (const phase of WORKFLOW_PHASES) {
      const items = state.phases[phase.id]?.items ?? [];
      const set = new Set(items.filter((i) => i.checked).map((i) => i.id));
      map.set(phase.id, set);
    }
    return map;
  }, [state]);

  const totalProgress = useMemo(() => {
    if (!state) return { done: 0, total: 0 };
    let done = 0;
    let total = 0;
    for (const phase of WORKFLOW_PHASES) {
      const items = state.phases[phase.id]?.items ?? [];
      for (const item of items) {
        total++;
        if (item.checked) done++;
      }
    }
    for (const item of state.ongoing?.items ?? []) {
      total++;
      if (item.checked) done++;
    }
    return { done, total };
  }, [state]);

  const ongoingChecked = useMemo(() => {
    const set = new Set<string>();
    for (const item of state?.ongoing?.items ?? []) {
      if (item.checked) set.add(item.id);
    }
    return set;
  }, [state]);

  const togglePhase = (phaseId: WorkflowPhaseId) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(phaseId)) next.delete(phaseId);
      else next.add(phaseId);
      return next;
    });
  };

  if (!state) {
    return (
      <div className="py-16 text-center text-slate-400">
        Loading workflow...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Today&apos;s Workflow</h1>
        <p className="text-slate-400 mt-1">{formatDate(today)}</p>
        <p className="text-sm text-slate-500 mt-2 max-w-2xl">
          Professional quant traders follow a structured routine. Use this checklist to build
          the same habits—even before you trade live.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <LaneSelector
          selected={state.selectedLane}
          onSelect={(id) => setSelectedLane(id as QuantLaneId)}
        />
      </div>

      {totalProgress.total > 0 && (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span>Progress: {totalProgress.done}/{totalProgress.total} items</span>
          <div className="flex-1 max-w-xs h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-blue-500/70 rounded-full transition-all"
              style={{ width: `${(totalProgress.done / totalProgress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      <div className="space-y-4">
        {WORKFLOW_PHASES.map((phase) => (
          <div key={phase.id}>
            <WorkflowPhaseSection
              phase={phase}
              checkedItems={checkedItemsByPhase.get(phase.id) ?? new Set()}
              onToggle={toggleItem}
              isExpanded={expandedPhases.has(phase.id)}
              onToggleExpand={() => togglePhase(phase.id)}
            />
            {phase.id === "pre-market" && (
              <div className="mt-4 grid gap-6 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                  <MarketStateForm
                    value={state.marketState}
                    onChange={setMarketState}
                  />
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                  <SessionSettingsForm
                    value={state.sessionSettings}
                    onChange={setSessionSettings}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="border-b border-slate-800 px-4 py-3">
          <h2 className="text-lg font-semibold text-slate-100">Ongoing Weekly / Monthly</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Where a lot of value is created. Research, backtest, improve systems, and collaborate.
          </p>
        </div>
        <div className="px-4 py-3 space-y-3">
          {ONGOING_WORKFLOW_ITEMS.map((item) => (
            <ChecklistItemRow
              key={item.id}
              item={item}
              checked={ongoingChecked.has(item.id)}
              onToggle={() => toggleOngoingItem(item.id)}
            />
          ))}
        </div>
      </section>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <p className="text-sm text-slate-400">
          <strong className="text-slate-300">Post-market analysis</strong> — Review your
          backtest results, equity curves, and trades in the{" "}
          <Link href="/dashboard" className="text-blue-400 hover:underline">
            Dashboard
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
