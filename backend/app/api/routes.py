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

TTM PREDICTIONS (Transformer):
- GET /api/prediction/ttm       → Prédiction TTM (Tiny Time Mixer)
- GET /api/prediction/ttm/status → Statut du modèle TTM

TRADING PLANS:
- GET /api/plans                → Liste des plans disponibles
- GET /api/plans/{id}           → Détail d'un plan
- POST /api/plans/{id}/execute  → Exécuter l'analyse avec un plan

ASSISTANT:
- POST /api/chat                → Chat avec l'assistant IA
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Any, List, Optional
import math
from datetime import datetime

from app.core.models import (
    MarketData, TechnicalAnalysis, TradingSignal, TradingPlan,
    PlanExecution, ChatRequest, ChatResponse, DemoHistoryResponse, DemoTradeRequest, OHLCV, MarketIntelligence
)
from app.services.binance_service import binance_service
from app.services.analysis_service import analysis_service
from app.services.demo_trading_service import demo_trading_service
from app.services.autonomous_trading_service import autonomous_trading_service
from app.services.learning_service import learning_service
from app.services.market_intelligence_service import market_intelligence_service
from app.ml.model import trading_model
from app.ml.model_v2 import trading_model_v2
from app.ml.prediction_service import prediction_service
from app.ml.ttm_prediction_service import ttm_prediction_service


router = APIRouter(prefix="/api", tags=["TraderPro API"])


# ============ DEMO TRADING (BINANCE TESTNET ONLY) ============

@router.post("/demo/execute")
async def execute_demo_trade(request: DemoTradeRequest):
    """Record the AI decision and attempt a Spot order on Binance Testnet only."""
    try:
        analysis = await analysis_service.get_full_analysis(request.symbol.upper(), request.timeframe)
        return await demo_trading_service.execute_signal(
            analysis.signal, request.symbol, request.amount_usdt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/history", response_model=DemoHistoryResponse)
async def get_demo_history():
    """Return decisions, open Testnet positions, closed trades and realised P&L."""
    try:
        return await demo_trading_service.history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/autonomous/status")
async def get_autonomous_status():
    """État du scheduler autonome et dernières expériences enregistrées."""
    return autonomous_trading_service.status()


@router.get("/learning/status")
async def get_learning_status():
    """Progression des expériences et registre champion/challenger."""
    autonomous_trading_service.sync_experiences()
    return learning_service.status()


@router.get("/intelligence/market", response_model=MarketIntelligence)
async def get_market_intelligence(symbol: str = Query(default="BTCUSDT")):
    """Contexte Futures public : funding, open interest, volatilité et régime."""
    return await market_intelligence_service.get_context(symbol)


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
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="1h"),
    days: int = Query(default=365, ge=220, le=730),
    horizon: int = Query(default=4, ge=1, le=24),
    threshold: float = Query(default=0.004, ge=0.001, le=0.05),
    grid_search: bool = Query(default=True, description="Recherche par grille avec validation temporelle ; plus lente mais recommandée.")
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
        metrics = trading_model.train(df, horizon=horizon, threshold=threshold, grid_search=grid_search)

        # Écrire l'artefact avant de répondre : un statut "success" signifie qu'il est durable.
        artifact_path = trading_model.save()

        return {
            "status": "success",
            "message": "Modèle entraîné avec succès",
            "metrics": metrics,
            "artifact_path": str(artifact_path),
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


@router.get("/model/v2/status")
async def get_model_v2_status():
    """Rapport du pipeline V2. Il reste séparé du bot tant que le walk-forward n'est pas positif."""
    if trading_model_v2.artifact_path.exists() and not trading_model_v2.is_trained:
        try:
            trading_model_v2.load()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Artefact V2 illisible : {exc}") from exc
    def json_safe(value: Any) -> Any:
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [json_safe(item) for item in value]
        return value

    return {
        "is_trained": trading_model_v2.is_trained,
        "eligible_for_testnet": bool(
            trading_model_v2.is_trained
            and trading_model_v2.metrics.get("walk_forward", {}).get("aggregate", {}).get("net_return", 0) > 0
        ),
        "metrics": json_safe(trading_model_v2.metrics) if trading_model_v2.is_trained else None,
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


# ============ TTM PREDICTIONS (Transformer) ============

@router.get("/prediction/ttm")
async def get_ttm_prediction(
    symbol: str = Query(default="BTCUSDT")
):
    """
    Obtenir la prédiction TTM (Tiny Time Mixer) pour demain

    TTM est un modèle Transformer léger d'IBM, fine-tuné sur les données BTC.
    Il prédit la direction (UP/DOWN) du prix pour le lendemain.

    Avantages par rapport au LSTM:
    - Architecture Transformer (attention mechanism)
    - Pré-entraîné sur de nombreuses séries temporelles
    - Meilleure capture des patterns long-terme

    Retourne:
    - prediction_for: Date de la prédiction (demain)
    - current_price: Prix actuel
    - prediction: Direction (UP/DOWN), confiance, probabilités
    - recommendation: Action suggérée
    - model_info: Informations sur le modèle TTM

    - **symbol**: Paire de trading (défaut: BTCUSDT)
    """
    try:
        # Vérifier si le modèle est disponible
        status = ttm_prediction_service.get_status()
        if not status['model_exists']:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Modèle TTM non disponible",
                    "message": "Le modèle TTM n'a pas été trouvé. Veuillez fine-tuner le modèle sur Colab et placer les fichiers dans backend/app/ml/models/ttm/",
                    "required_files": status.get('required_files', [
                        "config.json",
                        "model.safetensors",
                        "preprocessor.pkl",
                        "ttm_config.json"
                    ]),
                    "notebook": "colab_ttm_finetuning.ipynb"
                }
            )

        # Récupérer les données historiques (besoin de plus de données pour TTM)
        # Lire le context_length depuis la config du modèle si disponible
        ttm_config = ttm_prediction_service.config
        if ttm_config is None:
            # Essayer de charger la config
            import json
            config_path = ttm_prediction_service.config_path
            if config_path.exists():
                with open(config_path, 'r') as f:
                    ttm_config = json.load(f)

        context_length = ttm_config.get('context_length', 512) if ttm_config else 512
        df = await binance_service.get_historical_data(symbol, "1d", days=context_length + 60)

        if df.empty:
            raise HTTPException(status_code=404, detail="Pas de données disponibles")

        if len(df) < context_length:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de données historiques. Requis: {context_length} jours, Disponible: {len(df)}"
            )

        # Faire la prédiction
        prediction = await ttm_prediction_service.predict_tomorrow(df)

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction/ttm/status")
async def get_ttm_status():
    """
    Obtenir le statut du service de prédiction TTM

    Retourne:
    - is_loaded: Si le modèle est chargé en mémoire
    - model_exists: Si les fichiers du modèle existent
    - last_prediction_date: Date de la dernière prédiction
    - config: Configuration du modèle
    """
    return ttm_prediction_service.get_status()


@router.post("/prediction/ttm/refresh")
async def refresh_ttm_prediction():
    """
    Forcer le rafraîchissement de la prédiction TTM

    Efface le cache et force une nouvelle prédiction lors du prochain appel.
    """
    ttm_prediction_service.clear_cache()
    return {"status": "cache_cleared", "message": "Le cache TTM a été effacé. La prochaine prédiction sera recalculée."}


@router.get("/prediction/compare")
async def compare_predictions(
    symbol: str = Query(default="BTCUSDT")
):
    """
    Comparer les prédictions de tous les modèles disponibles

    Retourne les prédictions de:
    - LSTM (si disponible)
    - TTM (si disponible)
    - Consensus (si les deux sont d'accord)

    Utile pour avoir une vue d'ensemble et plus de confiance dans les signaux.
    """
    results = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "predictions": {},
        "consensus": None
    }

    # Récupérer les données une seule fois (assez pour TTM qui peut avoir besoin de 512+ jours)
    # Lire le context_length depuis la config TTM si disponible
    import json
    ttm_config = ttm_prediction_service.config
    if ttm_config is None:
        config_path = ttm_prediction_service.config_path
        if config_path.exists():
            with open(config_path, 'r') as f:
                ttm_config = json.load(f)

    context_length = ttm_config.get('context_length', 512) if ttm_config else 512
    df = await binance_service.get_historical_data(symbol, "1d", days=context_length + 60)

    if df.empty:
        raise HTTPException(status_code=404, detail="Pas de données disponibles")

    # Prédiction LSTM
    lstm_status = prediction_service.get_status()
    if lstm_status.get('model_exists'):
        try:
            lstm_pred = await prediction_service.predict_tomorrow(df)
            results["predictions"]["lstm"] = {
                "direction": lstm_pred["prediction"]["direction"],
                "confidence": lstm_pred["prediction"]["confidence"],
                "available": True
            }
        except Exception as e:
            results["predictions"]["lstm"] = {
                "available": False,
                "error": str(e)
            }
    else:
        results["predictions"]["lstm"] = {"available": False, "error": "Model not found"}

    # Prédiction TTM
    ttm_status = ttm_prediction_service.get_status()
    if ttm_status.get('model_exists'):
        try:
            ttm_pred = await ttm_prediction_service.predict_tomorrow(df)
            results["predictions"]["ttm"] = {
                "direction": ttm_pred["prediction"]["direction"],
                "confidence": ttm_pred["prediction"]["confidence"],
                "available": True
            }
        except Exception as e:
            results["predictions"]["ttm"] = {
                "available": False,
                "error": str(e)
            }
    else:
        results["predictions"]["ttm"] = {"available": False, "error": "Model not found"}

    # Calculer le consensus
    available_preds = [
        (name, pred) for name, pred in results["predictions"].items()
        if pred.get("available", False)
    ]

    if len(available_preds) >= 2:
        directions = [pred["direction"] for _, pred in available_preds]
        confidences = [pred["confidence"] for _, pred in available_preds]

        if len(set(directions)) == 1:
            # Tous les modèles sont d'accord
            results["consensus"] = {
                "direction": directions[0],
                "agreement": "FULL",
                "avg_confidence": sum(confidences) / len(confidences),
                "models_agreeing": len(available_preds)
            }
        else:
            # Les modèles ne sont pas d'accord
            results["consensus"] = {
                "direction": "MIXED",
                "agreement": "NONE",
                "recommendation": "Les modèles donnent des signaux contradictoires. Prudence recommandée."
            }
    elif len(available_preds) == 1:
        name, pred = available_preds[0]
        results["consensus"] = {
            "direction": pred["direction"],
            "agreement": "SINGLE_MODEL",
            "model": name,
            "confidence": pred["confidence"]
        }

    return results


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
