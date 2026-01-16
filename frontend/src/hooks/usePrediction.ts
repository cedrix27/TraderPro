"use client";

import { useState, useEffect, useCallback } from "react";
import {
  predictionApi,
  LSTMPrediction,
  PredictionStatus,
  ApiError,
} from "@/lib/api";

interface UsePredictionOptions {
  symbol?: string;
  autoFetch?: boolean;
}

interface UsePredictionReturn {
  prediction: LSTMPrediction | null;
  isLoading: boolean;
  error: string | null;
  errorDetails: any | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer la prédiction LSTM pour demain
 */
export function usePrediction(options: UsePredictionOptions = {}): UsePredictionReturn {
  const { symbol = "BTCUSDT", autoFetch = true } = options;

  const [prediction, setPrediction] = useState<LSTMPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<any | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setErrorDetails(null);
      const result = await predictionApi.getTomorrowPrediction(symbol);
      setPrediction(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        // Essayer de parser les détails de l'erreur
        try {
          const details = typeof err.message === 'string' ? JSON.parse(err.message) : err.message;
          setErrorDetails(details);
        } catch {
          setErrorDetails(null);
        }
      } else {
        setError("Erreur lors de la récupération de la prédiction");
      }
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [fetchData, autoFetch]);

  return { prediction, isLoading, error, errorDetails, refresh: fetchData };
}

interface UsePredictionStatusReturn {
  status: PredictionStatus | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook pour récupérer le statut du service de prédiction
 */
export function usePredictionStatus(): UsePredictionStatusReturn {
  const [status, setStatus] = useState<PredictionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await predictionApi.getStatus();
      setStatus(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Erreur lors de la récupération du statut");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { status, isLoading, error, refresh: fetchData };
}
