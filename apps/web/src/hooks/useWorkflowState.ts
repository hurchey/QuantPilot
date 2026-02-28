"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type MarketStateInputs,
  type OngoingWorkflowId,
  type QuantLaneId,
  type SessionSettings,
  type WorkflowPhaseId,
  type WorkflowState,
  loadWorkflowState,
  saveWorkflowState,
} from "@/lib/workflow-data";

export function useWorkflowState(date: Date) {
  const [state, setState] = useState<WorkflowState | null>(null);

  useEffect(() => {
    setState(loadWorkflowState(date));
  }, [date.toISOString().slice(0, 10)]);

  const persist = useCallback((next: WorkflowState) => {
    saveWorkflowState(next);
    setState(next);
  }, []);

  const toggleItem = useCallback(
    (phaseId: WorkflowPhaseId, itemId: string) => {
      if (!state) return;
      const phase = state.phases[phaseId];
      if (!phase) return;
      const items = phase.items.map((i) =>
        i.id === itemId ? { ...i, checked: !i.checked } : i
      );
      persist({
        ...state,
        phases: { ...state.phases, [phaseId]: { items } },
      });
    },
    [state, persist]
  );

  const toggleOngoingItem = useCallback(
    (itemId: OngoingWorkflowId) => {
      if (!state?.ongoing) return;
      const items = state.ongoing.items.map((i) =>
        i.id === itemId ? { ...i, checked: !i.checked } : i
      );
      persist({ ...state, ongoing: { items } });
    },
    [state, persist]
  );

  const setMarketState = useCallback(
    (marketState: MarketStateInputs) => {
      if (!state) return;
      persist({ ...state, marketState });
    },
    [state, persist]
  );

  const setSessionSettings = useCallback(
    (sessionSettings: SessionSettings) => {
      if (!state) return;
      persist({ ...state, sessionSettings });
    },
    [state, persist]
  );

  const setSelectedLane = useCallback(
    (lane: QuantLaneId) => {
      if (!state) return;
      persist({ ...state, selectedLane: lane });
    },
    [state, persist]
  );

  return {
    state,
    toggleItem,
    toggleOngoingItem,
    setMarketState,
    setSessionSettings,
    setSelectedLane,
  };
}
