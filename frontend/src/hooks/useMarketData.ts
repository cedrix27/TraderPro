"use client";

import { useState, useEffect, useCallback } from "react";
import { marketApi, MarketData, OHLCV, ApiError } from "@/lib/api";

interface UseMarketDataOptions {
  symbol?: string;
  refreshInterval?: number; // en millisecondes
  autoRefresh?: boolean;
}

interface UseMarketDataReturn {
  data: MarketData | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer les données de marché en temps réel
 */
export function useMarketData(
  options: UseMarketDataOptions = {}
): UseMarketDataReturn {
  const { symbol = "BTCUSDT", refreshInterval = 10000, autoRefresh = true } = options;

  const [data, setData] = useState<MarketData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const result = await marketApi.getPrice(symbol);
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération des données");
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

  return { data, isLoading, error, refresh: fetchData };
}

interface UseKlinesOptions {
  symbol?: string;
  interval?: string;
  limit?: number;
}

interface UseKlinesReturn {
  data: OHLCV[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer les données OHLCV (bougies)
 */
export function useKlines(options: UseKlinesOptions = {}): UseKlinesReturn {
  const { symbol = "BTCUSDT", interval = "1h", limit = 100 } = options;

  const [data, setData] = useState<OHLCV[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await marketApi.getKlines(symbol, interval, limit);
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération des bougies");
      }
    } finally {
      setIsLoading(false);
    }
  }, [symbol, interval, limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, isLoading, error, refresh: fetchData };
}
