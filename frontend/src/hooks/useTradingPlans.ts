"use client";

import { useState, useEffect, useCallback } from "react";
import {
  plansApi,
  TradingPlan,
  PlanExecution,
  ApiError,
} from "@/lib/api";

interface UseTradingPlansReturn {
  plans: TradingPlan[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer tous les plans de trading
 */
export function useTradingPlans(): UseTradingPlansReturn {
  const [plans, setPlans] = useState<TradingPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await plansApi.getAllPlans();
      setPlans(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération des plans");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { plans, isLoading, error, refresh: fetchData };
}

interface UsePlanExecutionOptions {
  planId: string;
  symbol?: string;
}

interface UsePlanExecutionReturn {
  execution: PlanExecution | null;
  isLoading: boolean;
  error: string | null;
  execute: () => Promise<void>;
}

/**
 * Hook pour exécuter un plan de trading
 */
export function usePlanExecution(
  options: UsePlanExecutionOptions
): UsePlanExecutionReturn {
  const { planId, symbol = "BTCUSDT" } = options;

  const [execution, setExecution] = useState<PlanExecution | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    if (!planId) return;

    try {
      setIsLoading(true);
      setError(null);
      const result = await plansApi.executePlan(planId, symbol);
      setExecution(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de l'exécution du plan");
      }
    } finally {
      setIsLoading(false);
    }
  }, [planId, symbol]);

  return { execution, isLoading, error, execute };
}
