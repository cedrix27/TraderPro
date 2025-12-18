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
