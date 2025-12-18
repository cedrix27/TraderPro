// Types pour TraderPro

export interface PriceData {
  time: number;
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

export interface SupportResistance {
  type: "support" | "resistance";
  price: number;
  strength: "strong" | "medium" | "weak";
}

export interface TradingSignal {
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  entry: number;
  stopLoss: number;
  takeProfit: number;
  riskReward: number;
  reasoning: string[];
}

export interface TradingPlan {
  id: string;
  name: string;
  description: string;
  timeframe: string;
  riskLevel: "low" | "medium" | "high";
  indicators: string[];
  icon: string;
}

export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  marketCap: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface AnalysisResult {
  trend: "bullish" | "bearish" | "neutral";
  trendStrength: number;
  indicators: Indicator[];
  supportResistance: SupportResistance[];
  signal: TradingSignal;
  summary: string;
}
