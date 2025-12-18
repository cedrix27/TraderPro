"use client";

import { useState, useEffect, useCallback } from "react";
import {
  analysisApi,
  TechnicalAnalysis,
  TradingSignal,
  ApiError,
} from "@/lib/api";

interface UseAnalysisOptions {
  symbol?: string;
  timeframe?: string;
  autoFetch?: boolean;
}

interface UseAnalysisReturn {
  analysis: TechnicalAnalysis | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer l'analyse technique complète
 */
export function useAnalysis(options: UseAnalysisOptions = {}): UseAnalysisReturn {
  const { symbol = "BTCUSDT", timeframe = "1h", autoFetch = true } = options;

  const [analysis, setAnalysis] = useState<TechnicalAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await analysisApi.getFullAnalysis(symbol, timeframe);
      setAnalysis(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération de l'analyse");
      }
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [fetchData, autoFetch]);

  return { analysis, isLoading, error, refresh: fetchData };
}

interface UseSignalOptions {
  symbol?: string;
  refreshInterval?: number;
  autoRefresh?: boolean;
}

interface UseSignalReturn {
  signal: TradingSignal | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer le signal de trading rapide
 */
export function useSignal(options: UseSignalOptions = {}): UseSignalReturn {
  const { symbol = "BTCUSDT", refreshInterval = 60000, autoRefresh = true } = options;

  const [signal, setSignal] = useState<TradingSignal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const result = await analysisApi.getSignal(symbol);
      setSignal(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération du signal");
      }
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();

    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refreshInterval, autoRefresh]);

  return { signal, isLoading, error, refresh: fetchData };
}
