"""
Routes API pour TraderPro

============ ENDPOINTS DISPONIBLES ============

MARKET DATA:
- GET /api/market/price         → Prix actuel BTC
- GET /api/market/klines        → Données OHLCV

ANALYSIS:
- GET /api/analysis             → Analyse technique complète
- GET /api/analysis/signal      → Signal de trading rapide
- GET /api/analysis/indicators  → Indicateurs uniquement

ML PREDICTIONS:
- GET /api/predict              → Prédiction du modèle ML
- POST /api/model/train         → Entraîner le modèle

LSTM PREDICTIONS:
- GET /api/prediction/tomorrow  → Prédiction OHLC pour demain (LSTM)
- GET /api/prediction/status    → Statut du modèle LSTM

TRADING PLANS:
- GET /api/plans                → Liste des plans disponibles
- GET /api/plans/{id}           → Détail d'un plan
- POST /api/plans/{id}/execute  → Exécuter l'analyse avec un plan

ASSISTANT:
- POST /api/chat                → Chat avec l'assistant IA
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from app.core.models import (
    MarketData, TechnicalAnalysis, TradingSignal, TradingPlan,
    PlanExecution, ChatRequest, ChatResponse, OHLCV
)
from app.services.binance_service import binance_service
from app.services.analysis_service import analysis_service
from app.ml.model import trading_model
from app.ml.prediction_service import prediction_service


router = APIRouter(prefix="/api", tags=["TraderPro API"])


# ============ MARKET DATA ============

@router.get("/market/price", response_model=MarketData)
async def get_current_price(symbol: str = Query(default="BTCUSDT")):
    """
    Obtenir le prix actuel et les stats 24h

    - **symbol**: Paire de trading (défaut: BTCUSDT)
    """
    try:
        return await binance_service.get_current_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/klines", response_model=List[OHLCV])
async def get_klines(
    symbol: str = Query(default="BTCUSDT"),
    interval: str = Query(default="1h"),
    limit: int = Query(default=100, le=1000)
):
    """
    Obtenir les données OHLCV (bougies)

    - **symbol**: Paire de trading
    - **interval**: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
    - **limit**: Nombre de bougies (max 1000)
    """
    try:
        return await binance_service.get_klines(symbol, interval, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ ANALYSIS ============

@router.get("/analysis", response_model=TechnicalAnalysis)
async def get_full_analysis(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="1h")
):
    """
    Obtenir une analyse technique complète

    Inclut:
    - Tendance générale et force
    - Tous les indicateurs (RSI, MACD, BB, etc.)
    - Moyennes mobiles
    - Supports et résistances
    - Signal de trading avec entry/SL/TP
    - Résumé textuel

    - **symbol**: Paire de trading
    - **timeframe**: Timeframe d'analyse
    """
    try:
        return await analysis_service.get_full_analysis(symbol, timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/signal", response_model=TradingSignal)
async def get_quick_signal(symbol: str = Query(default="BTCUSDT")):
    """
    Obtenir rapidement un signal de trading

    Retourne: action (BUY/SELL/HOLD), confidence, entry, SL, TP

    - **symbol**: Paire de trading
    """
    try:
        return await analysis_service.get_quick_signal(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ ML PREDICTIONS ============

@router.get("/predict")
async def get_ml_prediction(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="1h")
):
    """
    Obtenir une prédiction du modèle ML

    Retourne:
    - signal: 1 (BUY), 0 (HOLD), -1 (SELL)
    - confidence: Niveau de confiance en %
    - probabilities: Probabilités pour chaque classe

    - **symbol**: Paire de trading
    - **timeframe**: Timeframe d'analyse
    """
    try:
        if not trading_model.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Le modèle n'est pas entraîné. Utilisez POST /api/model/train d'abord."
            )

        # Récupérer les données
        df = await binance_service.get_historical_data(symbol, timeframe, days=60)

        if df.empty:
            raise HTTPException(status_code=404, detail="Pas de données disponibles")

        # Faire la prédiction
        signal, confidence, probabilities = trading_model.predict(df)

        signal_map = {1: "BUY", 0: "HOLD", -1: "SELL"}

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal_map[signal],
            "signal_code": signal,
            "confidence": round(confidence, 2),
            "probabilities": probabilities,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/train")
async def train_model(
    background_tasks: BackgroundTasks,
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="1h"),
    days: int = Query(default=90, ge=30, le=365),
    horizon: int = Query(default=4, ge=1, le=24),
    threshold: float = Query(default=0.02, ge=0.005, le=0.1)
):
    """
    Entraîner le modèle ML sur les données historiques

    ATTENTION: Cette opération peut prendre plusieurs minutes.

    - **symbol**: Paire de trading
    - **timeframe**: Timeframe d'analyse
    - **days**: Nombre de jours de données historiques
    - **horizon**: Horizon de prédiction (nombre de périodes)
    - **threshold**: Seuil de variation pour le labelling (ex: 0.02 = 2%)
    """
    try:
        # Récupérer les données
        df = await binance_service.get_historical_data(symbol, timeframe, days=days)

        if df.empty:
            raise HTTPException(status_code=404, detail="Pas de données disponibles")

        if len(df) < 500:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de données ({len(df)} lignes). Minimum 500 requis."
            )

        # Entraîner le modèle
        metrics = trading_model.train(df, horizon=horizon, threshold=threshold)

        # Sauvegarder en arrière-plan
        background_tasks.add_task(trading_model.save)

        return {
            "status": "success",
            "message": "Modèle entraîné avec succès",
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/status")
async def get_model_status():
    """Obtenir le statut du modèle ML"""
    return {
        "is_trained": trading_model.is_trained,
        "metrics": trading_model.metrics if trading_model.is_trained else None
    }


# ============ LSTM PREDICTIONS ============

@router.get("/prediction/tomorrow")
async def get_prediction_tomorrow(
    symbol: str = Query(default="BTCUSDT")
):
    """
    Obtenir la prédiction de direction pour demain (modèle LSTM Classification)

    Le modèle LSTM prédit si le prix va monter (UP) ou descendre (DOWN) demain.
    La prédiction est mise en cache et rafraîchie une fois par jour.

    Retourne:
    - prediction_for: Date de la prédiction (demain)
    - current_price: Prix actuel
    - prediction: Direction (UP/DOWN), confiance, probabilités
    - recommendation: Action suggérée, message, niveau de risque
    - model_info: Informations sur le modèle

    - **symbol**: Paire de trading (défaut: BTCUSDT)
    """
    try:
        # Vérifier si le modèle est disponible
        status = prediction_service.get_status()
        if not status['model_exists']:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Modèle LSTM non disponible",
                    "message": "Le modèle n'a pas été trouvé. Veuillez entraîner le modèle sur Colab et placer les fichiers dans backend/app/ml/models/",
                    "required_files": [
                        "btc_lstm_model_B.keras",
                        "btc_scaler_B.pkl",
                        "training_config_B.json"
                    ]
                }
            )

        # Récupérer les données historiques (30 jours suffisent pour Option B)
        df = await binance_service.get_historical_data(symbol, "1d", days=30)

        if df.empty:
            raise HTTPException(status_code=404, detail="Pas de données disponibles")

        if len(df) < 14:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de données historiques. Requis: 14 jours, Disponible: {len(df)}"
            )

        # Faire la prédiction
        prediction = await prediction_service.predict_tomorrow(df)

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction/status")
async def get_prediction_status():
    """
    Obtenir le statut du service de prédiction LSTM

    Retourne:
    - is_loaded: Si le modèle est chargé en mémoire
    - model_exists: Si les fichiers du modèle existent
    - last_prediction_date: Date de la dernière prédiction
    - config: Configuration du modèle
    """
    return prediction_service.get_status()


@router.post("/prediction/refresh")
async def refresh_prediction():
    """
    Forcer le rafraîchissement de la prédiction

    Efface le cache et force une nouvelle prédiction lors du prochain appel.
    """
    prediction_service.clear_cache()
    return {"status": "cache_cleared", "message": "Le cache a été effacé. La prochaine prédiction sera recalculée."}


# ============ TRADING PLANS ============

# Plans de trading prédéfinis
TRADING_PLANS = {
    "scalping": TradingPlan(
        id="scalping",
        name="Scalping",
        description="Trading à très court terme. Profitez des petits mouvements de prix.",
        timeframe="5m",
        risk_level="high",
        indicators=["RSI", "MACD", "Volume", "BB"],
        rules={
            "entry": ["RSI < 30 ou > 70", "Croisement MACD"],
            "exit": ["Take profit 0.5-1%", "Stop loss 0.3%"],
            "management": ["Max 3 trades simultanés"]
        }
    ),
    "swing": TradingPlan(
        id="swing",
        name="Swing Trading",
        description="Trading à moyen terme. Capturez les mouvements sur plusieurs jours.",
        timeframe="4h",
        risk_level="medium",
        indicators=["MA50", "MA200", "RSI", "Support/Résistance"],
        rules={
            "entry": ["Prix au-dessus MA50", "Rebond sur support"],
            "exit": ["Take profit sur résistance", "Stop loss sous swing low"],
            "management": ["Risque max 2% par trade", "R/R minimum 1:2"]
        }
    ),
    "position": TradingPlan(
        id="position",
        name="Position Trading",
        description="Trading à long terme. Investissez sur les tendances de fond.",
        timeframe="1d",
        risk_level="low",
        indicators=["MA200", "Tendance Weekly", "Support historique"],
        rules={
            "entry": ["Tendance weekly confirmée", "Prix au-dessus MA200"],
            "exit": ["Take profit progressif", "Stop loss 10-15%"],
            "management": ["DCA recommandé", "Position sizing conservateur"]
        }
    )
}


@router.get("/plans", response_model=List[TradingPlan])
async def get_trading_plans():
    """Obtenir la liste des plans de trading disponibles"""
    return list(TRADING_PLANS.values())


@router.get("/plans/{plan_id}", response_model=TradingPlan)
async def get_trading_plan(plan_id: str):
    """Obtenir les détails d'un plan de trading"""
    if plan_id not in TRADING_PLANS:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    return TRADING_PLANS[plan_id]


@router.post("/plans/{plan_id}/execute", response_model=PlanExecution)
async def execute_trading_plan(
    plan_id: str,
    symbol: str = Query(default="BTCUSDT")
):
    """
    Exécuter l'analyse avec un plan de trading spécifique

    Retourne l'analyse adaptée au plan sélectionné avec
    des recommandations personnalisées.

    - **plan_id**: ID du plan (scalping, swing, position)
    - **symbol**: Paire de trading
    """
    if plan_id not in TRADING_PLANS:
        raise HTTPException(status_code=404, detail="Plan non trouvé")

    plan = TRADING_PLANS[plan_id]

    try:
        # Effectuer l'analyse avec le timeframe du plan
        analysis = await analysis_service.get_full_analysis(
            symbol=symbol,
            timeframe=plan.timeframe
        )

        # Générer des recommandations basées sur le plan
        recommendations = []
        warnings = []

        if analysis.signal.action.value == "BUY":
            recommendations.append(f"Signal d'achat détecté avec {analysis.signal.confidence}% de confiance")
            recommendations.append(f"Entry suggéré: ${analysis.signal.entry:,.2f}")
            recommendations.append(f"Stop Loss: ${analysis.signal.stop_loss:,.2f}")
            recommendations.append(f"Take Profit: ${analysis.signal.take_profit:,.2f}")
        elif analysis.signal.action.value == "SELL":
            recommendations.append(f"Signal de vente détecté avec {analysis.signal.confidence}% de confiance")
            warnings.append("Considérez de réduire ou fermer vos positions longues")
        else:
            recommendations.append("Pas de signal clair - Attendez une meilleure opportunité")

        # Avertissements basés sur le plan
        if plan.risk_level == "high":
            warnings.append("Ce plan est à haut risque. Ne tradez qu'avec du capital que vous pouvez perdre.")

        if analysis.signal.risk_reward < 2:
            warnings.append(f"Le ratio Risk/Reward ({analysis.signal.risk_reward:.1f}) est inférieur à 2. Soyez prudent.")

        return PlanExecution(
            plan_id=plan_id,
            analysis=analysis,
            recommendations=recommendations,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ ASSISTANT CHAT ============

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Discuter avec l'assistant IA

    L'assistant peut:
    - Répondre aux questions sur le trading
    - Fournir des analyses en temps réel
    - Donner des conseils basés sur le contexte

    - **message**: Votre question ou message
    - **context**: Contexte optionnel (ex: plan actif)
    """
    try:
        message = request.message.lower()

        # Réponses basées sur les mots-clés
        if any(word in message for word in ["tendance", "trend", "direction"]):
            analysis = await analysis_service.get_full_analysis("BTCUSDT")
            response = f"""📊 **Analyse de la tendance BTC**

La tendance actuelle est **{analysis.trend.value}** avec une force de {analysis.trend_strength:.0f}%.

{analysis.summary}

Signal: **{analysis.signal.action.value}** (Confiance: {analysis.signal.confidence}%)"""

            return ChatResponse(
                message=response,
                analysis=analysis,
                signal=analysis.signal
            )

        elif any(word in message for word in ["support", "résistance", "resistance", "niveau"]):
            analysis = await analysis_service.get_full_analysis("BTCUSDT")
            supports = [sr for sr in analysis.support_resistance if sr.type == "support"]
            resistances = [sr for sr in analysis.support_resistance if sr.type == "resistance"]

            response = f"""🎯 **Niveaux clés pour BTC**

**Résistances:**
{chr(10).join([f'• ${r.price:,.0f} ({r.strength.value})' for r in resistances])}

**Supports:**
{chr(10).join([f'• ${s.price:,.0f} ({s.strength.value})' for s in supports])}

Prix actuel: Surveillez la réaction sur ces niveaux pour des opportunités."""

            return ChatResponse(message=response)

        elif any(word in message for word in ["acheter", "buy", "achat", "entrer"]):
            analysis = await analysis_service.get_full_analysis("BTCUSDT")

            if analysis.signal.action.value == "BUY":
                response = f"""💡 **Signal d'achat actif!**

L'analyse indique une opportunité d'achat:
• Entry: ${analysis.signal.entry:,.2f}
• Stop Loss: ${analysis.signal.stop_loss:,.2f}
• Take Profit: ${analysis.signal.take_profit:,.2f}
• Risk/Reward: 1:{analysis.signal.risk_reward:.1f}
• Confiance: {analysis.signal.confidence}%

⚠️ Rappel: Ne risquez jamais plus de 2% de votre capital par trade."""
            else:
                response = f"""⏸️ **Pas de signal d'achat pour le moment**

Le signal actuel est: **{analysis.signal.action.value}**
Confiance: {analysis.signal.confidence}%

Il est recommandé d'attendre un meilleur setup. Les conditions actuelles ne sont pas optimales pour un achat."""

            return ChatResponse(message=response, signal=analysis.signal)

        else:
            # Réponse par défaut
            return ChatResponse(
                message="""Je suis votre assistant de trading IA spécialisé sur le Bitcoin.

Je peux vous aider avec:
• **Tendances**: "Quelle est la tendance actuelle?"
• **Niveaux clés**: "Quels sont les supports et résistances?"
• **Trading**: "Dois-je acheter maintenant?"
• **Analyse**: "Fais-moi une analyse technique"

Posez-moi votre question!"""
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH CHECK ============

@router.get("/health")
async def health_check():
    """Vérifier que l'API fonctionne"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
