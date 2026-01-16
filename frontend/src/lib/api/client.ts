/**
 * Client API pour communiquer avec le backend FastAPI
 *
 * Ce fichier centralise toutes les communications avec le backend.
 * Il gère les erreurs, les timeouts, et la configuration de base.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Erreur personnalisée pour les appels API
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Fonction de base pour les appels API
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        response.statusText,
        errorData.detail || `Erreur API: ${response.status}`
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Erreur réseau
    throw new ApiError(0, "Network Error", "Impossible de contacter le serveur");
  }
}

// ============ TYPES ============

export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  change_percent_24h: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  timestamp: string;
}

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Indicator {
  name: string;
  value: number;
  signal: "bullish" | "bearish" | "neutral";
  description: string;
}

export interface MovingAverage {
  name: string;
  period: number;
  value: number;
  signal: "bullish" | "bearish";
}

export interface SupportResistance {
  type: "support" | "resistance";
  price: number;
  strength: "strong" | "medium" | "weak";
  touches: number;
}

export interface TradingSignal {
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  entry: number;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  reasoning: string[];
  timestamp: string;
}

export interface TechnicalAnalysis {
  symbol: string;
  timeframe: string;
  trend: "bullish" | "bearish" | "neutral";
  trend_strength: number;
  indicators: Indicator[];
  moving_averages: MovingAverage[];
  support_resistance: SupportResistance[];
  signal: TradingSignal;
  summary: string;
  timestamp: string;
}

export interface TradingPlan {
  id: string;
  name: string;
  description: string;
  timeframe: string;
  risk_level: "low" | "medium" | "high";
  indicators: string[];
  rules: Record<string, string[]>;
}

export interface PlanExecution {
  plan_id: string;
  analysis: TechnicalAnalysis;
  recommendations: string[];
  warnings: string[];
}

export interface MLPrediction {
  symbol: string;
  timeframe: string;
  signal: string;
  signal_code: number;
  confidence: number;
  probabilities: {
    BUY: number;
    HOLD: number;
    SELL: number;
  };
  timestamp: string;
}

export interface ModelStatus {
  is_trained: boolean;
  metrics: {
    accuracy: number;
    classification_report: Record<string, any>;
    top_features: { feature: string; importance: number }[];
    trained_at: string;
  } | null;
}

export interface LSTMPrediction {
  prediction_for: string;
  generated_at: string;
  current_price: {
    close: number;
    date: string;
  };
  prediction: {
    direction: "UP" | "DOWN";
    confidence: number;
    signal_strength: "STRONG" | "MODERATE" | "WEAK";
    probabilities: {
      UP: number;
      DOWN: number;
    };
  };
  recommendation: {
    action: "CONSIDER_BUY" | "CONSIDER_SELL" | "WATCH" | "HOLD";
    message: string;
    risk_level: "LOW" | "MODERATE" | "HIGH";
  };
  model_info: {
    version: string;
    type: string;
    trained_at: string;
    sequence_length: number;
    metrics: Record<string, any>;
  };
}

export interface PredictionStatus {
  is_loaded: boolean;
  model_path: string;
  model_exists: boolean;
  scaler_exists: boolean;
  config_exists: boolean;
  last_prediction_date: string | null;
  config: Record<string, any> | null;
}

export interface ChatResponse {
  message: string;
  analysis?: TechnicalAnalysis;
  signal?: TradingSignal;
}

// ============ API FUNCTIONS ============

/**
 * Market Data
 */
export const marketApi = {
  /**
   * Obtenir le prix actuel
   */
  getPrice: (symbol: string = "BTCUSDT"): Promise<MarketData> =>
    fetchApi(`/market/price?symbol=${symbol}`),

  /**
   * Obtenir les données OHLCV (bougies)
   */
  getKlines: (
    symbol: string = "BTCUSDT",
    interval: string = "1h",
    limit: number = 100
  ): Promise<OHLCV[]> =>
    fetchApi(`/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`),
};

/**
 * Analysis
 */
export const analysisApi = {
  /**
   * Obtenir l'analyse technique complète
   */
  getFullAnalysis: (
    symbol: string = "BTCUSDT",
    timeframe: string = "1h"
  ): Promise<TechnicalAnalysis> =>
    fetchApi(`/analysis?symbol=${symbol}&timeframe=${timeframe}`),

  /**
   * Obtenir un signal rapide
   */
  getSignal: (symbol: string = "BTCUSDT"): Promise<TradingSignal> =>
    fetchApi(`/analysis/signal?symbol=${symbol}`),
};

/**
 * ML Predictions
 */
export const mlApi = {
  /**
   * Obtenir une prédiction ML
   */
  getPrediction: (
    symbol: string = "BTCUSDT",
    timeframe: string = "1h"
  ): Promise<MLPrediction> =>
    fetchApi(`/predict?symbol=${symbol}&timeframe=${timeframe}`),

  /**
   * Entraîner le modèle
   */
  trainModel: (
    symbol: string = "BTCUSDT",
    timeframe: string = "1h",
    days: number = 90,
    horizon: number = 4,
    threshold: number = 0.02
  ): Promise<{ status: string; message: string; metrics: any }> =>
    fetchApi(
      `/model/train?symbol=${symbol}&timeframe=${timeframe}&days=${days}&horizon=${horizon}&threshold=${threshold}`,
      { method: "POST" }
    ),

  /**
   * Obtenir le statut du modèle
   */
  getModelStatus: (): Promise<ModelStatus> =>
    fetchApi("/model/status"),
};

/**
 * Trading Plans
 */
export const plansApi = {
  /**
   * Obtenir tous les plans
   */
  getAllPlans: (): Promise<TradingPlan[]> =>
    fetchApi("/plans"),

  /**
   * Obtenir un plan spécifique
   */
  getPlan: (planId: string): Promise<TradingPlan> =>
    fetchApi(`/plans/${planId}`),

  /**
   * Exécuter un plan
   */
  executePlan: (
    planId: string,
    symbol: string = "BTCUSDT"
  ): Promise<PlanExecution> =>
    fetchApi(`/plans/${planId}/execute?symbol=${symbol}`, { method: "POST" }),
};

/**
 * Chat Assistant
 */
export const chatApi = {
  /**
   * Envoyer un message au chatbot
   */
  sendMessage: (
    message: string,
    context?: Record<string, any>
  ): Promise<ChatResponse> =>
    fetchApi("/chat", {
      method: "POST",
      body: JSON.stringify({ message, context }),
    }),
};

/**
 * LSTM Predictions (Prédiction du prix pour demain)
 */
export const predictionApi = {
  /**
   * Obtenir la prédiction OHLC pour demain
   */
  getTomorrowPrediction: (symbol: string = "BTCUSDT"): Promise<LSTMPrediction> =>
    fetchApi(`/prediction/tomorrow?symbol=${symbol}`),

  /**
   * Obtenir le statut du service de prédiction
   */
  getStatus: (): Promise<PredictionStatus> =>
    fetchApi("/prediction/status"),

  /**
   * Forcer le rafraîchissement de la prédiction
   */
  refresh: (): Promise<{ status: string; message: string }> =>
    fetchApi("/prediction/refresh", { method: "POST" }),
};

/**
 * Health Check
 */
export const healthApi = {
  /**
   * Vérifier si l'API est en ligne
   */
  check: (): Promise<{ status: string; timestamp: string; version: string }> =>
    fetchApi("/health"),
};
