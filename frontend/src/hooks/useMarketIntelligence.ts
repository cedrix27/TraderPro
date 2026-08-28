"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, intelligenceApi, MarketIntelligence } from "@/lib/api";

export function useMarketIntelligence(symbol = "BTCUSDT") {
  const [data, setData] = useState<MarketIntelligence | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setData(await intelligenceApi.getMarketContext(symbol));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Contexte Futures indisponible");
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60_000);
    return () => clearInterval(interval);
  }, [refresh]);

  return { data, isLoading, error, refresh };
}
