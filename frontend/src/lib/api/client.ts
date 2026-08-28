/**
 * Client API pour communiquer avec le backend FastAPI
 *
 * Ce fichier centralise toutes les communications avec le backend.
 * Il gère les erreurs, les timeouts, et la configuration de base.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api";

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

export interface MarketIntelligence {
  symbol: string;
  price: number;
  day_change_pct: number;
  funding_rate_pct: number;
  open_interest: number;
  open_interest_change_pct: number | null;
  volatility_pct: number;
  regime: "trend_up" | "trend_down" | "range" | "high_volatility";
  bias: "bullish" | "bearish" | "neutral";
  context_score: number;
  recommendation: string;
  sources: string[];
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
    classification_report: Record<string, unknown>;
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
    metrics: Record<string, unknown>;
  };
}

export interface PredictionStatus {
  is_loaded: boolean;
  model_path: string;
  model_exists: boolean;
  scaler_exists: boolean;
  config_exists: boolean;
  last_prediction_date: string | null;
  config: Record<string, unknown> | null;
}

export interface TTMPrediction {
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
    raw_value: number;
    probabilities: {
      UP: number;
      DOWN: number;
    };
  };
  recommendation: {
    action: string;
    text: string;
    confidence_level: string;
    disclaimer: string;
  };
  model_info: {
    type: string;
    version: string;
    base_model: string;
    context_length: number;
    trained_at: string;
    metrics: Record<string, unknown>;
  };
}

export interface TTMStatus {
  service: string;
  is_loaded: boolean;
  model_path: string;
  model_exists: boolean;
  preprocessor_exists: boolean;
  config_exists: boolean;
  last_prediction_date: string | null;
  cache_active: boolean;
  config: Record<string, unknown> | null;
  required_files: string[];
}

export interface PredictionComparison {
  symbol: string;
  timestamp: string;
  predictions: {
    lstm?: {
      direction?: string;
      confidence?: number;
      available: boolean;
      error?: string;
    };
    ttm?: {
      direction?: string;
      confidence?: number;
      available: boolean;
      error?: string;
    };
  };
  consensus: {
    direction: string;
    agreement: "FULL" | "NONE" | "SINGLE_MODEL";
    avg_confidence?: number;
    models_agreeing?: number;
    model?: string;
    confidence?: number;
    recommendation?: string;
  } | null;
}

export interface ChatResponse {
  message: string;
  analysis?: TechnicalAnalysis;
  signal?: TradingSignal;
}

export interface DemoDecision {
  id: number;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  amount_usdt: number;
  reasoning: string[];
  status: "executed" | "recorded" | "rejected";
  rejection_reason: string | null;
  created_at: string;
}

export interface DemoPosition {
  id: number;
  decision_id: number;
  symbol: string;
  side: "LONG" | "SHORT";
  quantity: number;
  entry_price: number;
  amount_usdt: number;
  current_price: number | null;
  unrealized_pnl_usdt: number | null;
  opened_at: string;
}

export interface DemoTradeHistory {
  id: number;
  decision_id: number;
  symbol: string;
  side: "LONG" | "SHORT";
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  amount_usdt: number;
  pnl_usdt: number | null;
  status: "open" | "closed" | "rejected";
  is_testnet: boolean;
  leverage: number;
  margin_mode: "ISOLATED";
  liquidation_price: number | null;
  opened_at: string;
  closed_at: string | null;
}

export interface DemoHistoryResponse {
  mode: "binance_usdt_m_futures_testnet";
  decisions: DemoDecision[];
  open_positions: DemoPosition[];
  trades: DemoTradeHistory[];
  realized_pnl_usdt: number;
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

export const intelligenceApi = {
  getMarketContext: (symbol: string = "BTCUSDT"): Promise<MarketIntelligence> =>
    fetchApi(`/intelligence/market?symbol=${symbol}`),
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
  ): Promise<{ status: string; message: string; metrics: Record<string, unknown> }> =>
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

/** Binance Spot Testnet paper-trading journal. No production Binance endpoint is used. */
export const demoTradingApi = {
  execute: (symbol: string, amount_usdt: number, timeframe: string = "1h"): Promise<DemoDecision> =>
    fetchApi("/demo/execute", {
      method: "POST",
      body: JSON.stringify({ symbol, amount_usdt, timeframe }),
    }),
  getHistory: (): Promise<DemoHistoryResponse> => fetchApi("/demo/history"),
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
    context?: Record<string, unknown>
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
   * Obtenir la prédiction LSTM pour demain
   */
  getLSTMPrediction: (symbol: string = "BTCUSDT"): Promise<LSTMPrediction> =>
    fetchApi(`/prediction/tomorrow?symbol=${symbol}`),

  /**
   * Alias pour compatibilité
   */
  getTomorrowPrediction: (symbol: string = "BTCUSDT"): Promise<LSTMPrediction> =>
    fetchApi(`/prediction/tomorrow?symbol=${symbol}`),

  /**
   * Obtenir le statut du service de prédiction LSTM
   */
  getStatus: (): Promise<PredictionStatus> =>
    fetchApi("/prediction/status"),

  /**
   * Forcer le rafraîchissement de la prédiction LSTM
   */
  refresh: (): Promise<{ status: string; message: string }> =>
    fetchApi("/prediction/refresh", { method: "POST" }),

  /**
   * Obtenir la prédiction TTM pour demain
   */
  getTTMPrediction: (symbol: string = "BTCUSDT"): Promise<TTMPrediction> =>
    fetchApi(`/prediction/ttm?symbol=${symbol}`),

  /**
   * Obtenir le statut du service TTM
   */
  getTTMStatus: (): Promise<TTMStatus> =>
    fetchApi("/prediction/ttm/status"),

  /**
   * Forcer le rafraîchissement de la prédiction TTM
   */
  refreshTTM: (): Promise<{ status: string; message: string }> =>
    fetchApi("/prediction/ttm/refresh", { method: "POST" }),

  /**
   * Comparer les prédictions de tous les modèles
   */
  comparePredictions: (symbol: string = "BTCUSDT"): Promise<PredictionComparison> =>
    fetchApi(`/prediction/compare?symbol=${symbol}`),
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
