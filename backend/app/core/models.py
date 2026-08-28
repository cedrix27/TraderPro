"""
Modèles Pydantic pour l'API TraderPro
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TrendType(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StrengthLevel(str, Enum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


# ============ Data Models ============

class OHLCV(BaseModel):
    """Données de prix OHLCV (Open, High, Low, Close, Volume)"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketData(BaseModel):
    """Données de marché en temps réel"""
    symbol: str
    price: float
    change_24h: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    timestamp: datetime = Field(default_factory=datetime.now)


class MarketIntelligence(BaseModel):
    """Contexte Futures public utilisé pour expliquer, puis améliorer, les décisions."""
    symbol: str
    price: float
    day_change_pct: float
    funding_rate_pct: float
    open_interest: float
    open_interest_change_pct: Optional[float] = None
    volatility_pct: float
    regime: Literal["trend_up", "trend_down", "range", "high_volatility"]
    bias: Literal["bullish", "bearish", "neutral"]
    context_score: float = Field(ge=0, le=100)
    recommendation: str
    sources: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


# ============ Indicator Models ============

class Indicator(BaseModel):
    """Un indicateur technique"""
    name: str
    value: float
    signal: TrendType
    description: str


class MovingAverage(BaseModel):
    """Moyenne mobile"""
    name: str
    period: int
    value: float
    signal: TrendType


class SupportResistance(BaseModel):
    """Niveau de support ou résistance"""
    type: Literal["support", "resistance"]
    price: float
    strength: StrengthLevel
    touches: int = 0


# ============ Signal Models ============

class TradingSignal(BaseModel):
    """Signal de trading généré par l'IA"""
    action: SignalType
    confidence: float = Field(ge=0, le=100)
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasoning: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


# ============ Analysis Models ============

class TechnicalAnalysis(BaseModel):
    """Résultat d'analyse technique complète"""
    symbol: str
    timeframe: str
    trend: TrendType
    trend_strength: float = Field(ge=0, le=100)
    indicators: List[Indicator]
    moving_averages: List[MovingAverage]
    support_resistance: List[SupportResistance]
    signal: TradingSignal
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)


# ============ Trading Plan Models ============

class TradingPlan(BaseModel):
    """Plan de trading"""
    id: str
    name: str
    description: str
    timeframe: str
    risk_level: RiskLevel
    indicators: List[str]
    rules: dict


class PlanExecution(BaseModel):
    """Exécution d'un plan de trading"""
    plan_id: str
    analysis: TechnicalAnalysis
    recommendations: List[str]
    warnings: List[str]


# ============ Request/Response Models ============

class AnalysisRequest(BaseModel):
    """Requête d'analyse"""
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    plan_id: Optional[str] = None


class PredictionRequest(BaseModel):
    """Requête de prédiction"""
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    horizon: int = 4  # Nombre de périodes à prédire


class ChatMessage(BaseModel):
    """Message du chat avec l'assistant IA"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Requête au chatbot"""
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Réponse du chatbot"""
    message: str
    analysis: Optional[TechnicalAnalysis] = None
    signal: Optional[TradingSignal] = None


# ============ Paper Trading / Binance Testnet ============

class DemoTradeRequest(BaseModel):
    """Request a decision and, if applicable, a Binance Spot Testnet order."""
    symbol: str = Field(default="BTCUSDT", min_length=5, max_length=20)
    amount_usdt: float = Field(default=25, gt=0, le=10_000)
    timeframe: str = "1h"


class DemoDecision(BaseModel):
    id: int
    symbol: str
    action: SignalType
    confidence: float
    amount_usdt: float
    reasoning: List[str]
    status: Literal["executed", "recorded", "rejected"]
    rejection_reason: Optional[str] = None
    created_at: datetime


class DemoPosition(BaseModel):
    id: int
    decision_id: int
    symbol: str
    side: Literal["LONG", "SHORT"]
    quantity: float
    entry_price: float
    amount_usdt: float
    current_price: Optional[float] = None
    unrealized_pnl_usdt: Optional[float] = None
    opened_at: datetime


class DemoTradeHistory(BaseModel):
    id: int
    decision_id: int
    symbol: str
    side: Literal["LONG", "SHORT"]
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    amount_usdt: float
    pnl_usdt: Optional[float] = None
    status: Literal["open", "closed", "rejected"]
    is_testnet: bool
    leverage: int = 1
    margin_mode: Literal["ISOLATED"] = "ISOLATED"
    liquidation_price: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None


class DemoHistoryResponse(BaseModel):
    mode: Literal["binance_usdt_m_futures_testnet"]
    decisions: List[DemoDecision]
    open_positions: List[DemoPosition]
    trades: List[DemoTradeHistory]
    realized_pnl_usdt: float
