"""
Service d'analyse qui combine les indicateurs et génère des signaux de trading

Ce service implémente la logique d'un trader professionnel:
1. Analyse du contexte (tendance générale)
2. Identification des zones clés (support/résistance)
3. Génération de signaux avec gestion du risque
"""
import pandas as pd
from typing import List, Optional
from datetime import datetime
from app.core.models import (
    TechnicalAnalysis, TradingSignal, SignalType, TrendType,
    Indicator, MovingAverage, SupportResistance
)
from app.services.binance_service import binance_service
from app.services.indicators_service import indicators_service


class AnalysisService:
    """
    Service principal d'analyse technique

    ============ LOGIQUE D'UN TRADER PRO ============

    Un trader professionnel suit généralement ces étapes:

    1. CONTEXTE (Macro)
       - Quelle est la tendance sur les timeframes supérieurs?
       - Le marché est-il en tendance ou en range?

    2. ZONES CLÉS
       - Où sont les supports et résistances majeurs?
       - Le prix est-il proche d'une zone importante?

    3. TIMING
       - Les indicateurs confirment-ils le mouvement?
       - Y a-t-il convergence de plusieurs signaux?

    4. GESTION DU RISQUE
       - Où placer le stop-loss?
       - Quel est le ratio risk/reward?
       - Quelle taille de position?

    5. EXÉCUTION
       - Entry précis (limit order vs market)
       - Take profit (un ou plusieurs niveaux)
    """

    def __init__(self):
        self.binance = binance_service
        self.indicators = indicators_service

    async def get_full_analysis(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h"
    ) -> TechnicalAnalysis:
        """
        Effectuer une analyse technique complète

        Args:
            symbol: Paire de trading
            timeframe: Timeframe d'analyse

        Returns:
            TechnicalAnalysis avec tous les détails
        """
        # 1. Récupérer les données historiques
        df = await self.binance.get_historical_data(
            symbol=symbol,
            interval=timeframe,
            days=60  # 60 jours pour avoir assez de données pour les MAs
        )

        if df.empty:
            raise ValueError(f"Pas de données disponibles pour {symbol}")

        # 2. Calculer tous les indicateurs
        analysis_data = self.indicators.calculate_all_indicators(df)

        # 3. Générer le signal de trading
        signal = self._generate_trading_signal(
            df=df,
            analysis_data=analysis_data
        )

        # 4. Générer le résumé
        summary = self._generate_summary(analysis_data, signal)

        return TechnicalAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            trend=analysis_data["trend"],
            trend_strength=analysis_data["trend_strength"],
            indicators=analysis_data["indicators"],
            moving_averages=analysis_data["moving_averages"],
            support_resistance=analysis_data["support_resistance"],
            signal=signal,
            summary=summary,
            timestamp=datetime.now()
        )

    def _generate_trading_signal(
        self,
        df: pd.DataFrame,
        analysis_data: dict
    ) -> TradingSignal:
        """
        Générer un signal de trading basé sur l'analyse

        Logique de décision:
        1. Évaluer le score global (indicateurs + MAs)
        2. Vérifier les confirmations
        3. Calculer entry, stop-loss, take-profit
        """
        current_price = analysis_data["current_price"]
        atr = analysis_data["atr"]
        trend = analysis_data["trend"]
        sr_levels = analysis_data["support_resistance"]

        # Calculer le score de signal
        score = 0
        reasoning = []

        # Score basé sur les indicateurs
        for indicator in analysis_data["indicators"]:
            if indicator.signal == TrendType.BULLISH:
                score += 1
                reasoning.append(f"{indicator.name}: Signal haussier")
            elif indicator.signal == TrendType.BEARISH:
                score -= 1
                reasoning.append(f"{indicator.name}: Signal baissier")

        # Score basé sur les MAs
        for ma in analysis_data["moving_averages"]:
            if ma.signal == TrendType.BULLISH:
                score += 1
            else:
                score -= 1

        # Bonus pour Golden Cross / Death Cross
        raw = analysis_data["raw"]
        if raw["sma_50"].iloc[-1] > raw["sma_200"].iloc[-1]:
            if raw["sma_50"].iloc[-5] < raw["sma_200"].iloc[-5]:
                score += 2
                reasoning.append("Golden Cross récent détecté")

        # Trouver les niveaux de S/R les plus proches
        supports = [s for s in sr_levels if s.type == "support"]
        resistances = [r for r in sr_levels if r.type == "resistance"]

        nearest_support = supports[0].price if supports else current_price * 0.95
        nearest_resistance = resistances[0].price if resistances else current_price * 1.05

        # Déterminer le signal
        total_signals = len(analysis_data["indicators"]) + len(analysis_data["moving_averages"])
        confidence = min(100, max(0, 50 + (score / total_signals) * 50))

        if score >= 3:
            action = SignalType.BUY
            entry = current_price
            stop_loss = max(nearest_support * 0.99, current_price - 2 * atr)
            take_profit = min(nearest_resistance, current_price + 3 * atr)
            reasoning.insert(0, f"Tendance haussière confirmée ({score} signaux positifs)")
        elif score <= -3:
            action = SignalType.SELL
            entry = current_price
            stop_loss = min(nearest_resistance * 1.01, current_price + 2 * atr)
            take_profit = max(nearest_support, current_price - 3 * atr)
            reasoning.insert(0, f"Tendance baissière confirmée ({abs(score)} signaux négatifs)")
        else:
            action = SignalType.HOLD
            entry = current_price
            stop_loss = current_price - 1.5 * atr
            take_profit = current_price + 1.5 * atr
            reasoning.insert(0, "Signaux mixtes - Attendre une confirmation")

        # Calculer le ratio Risk/Reward
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        risk_reward = reward / risk if risk > 0 else 0

        return TradingSignal(
            action=action,
            confidence=round(confidence, 1),
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=round(risk_reward, 2),
            reasoning=reasoning[:5],  # Top 5 raisons
            timestamp=datetime.now()
        )

    def _generate_summary(self, analysis_data: dict, signal: TradingSignal) -> str:
        """Générer un résumé textuel de l'analyse"""
        trend = analysis_data["trend"]
        trend_strength = analysis_data["trend_strength"]

        trend_desc = {
            TrendType.BULLISH: "haussière",
            TrendType.BEARISH: "baissière",
            TrendType.NEUTRAL: "neutre"
        }

        summary = f"La tendance actuelle est {trend_desc[trend]} avec une force de {trend_strength:.0f}%. "

        # Ajouter info sur les MAs
        bullish_mas = sum(1 for ma in analysis_data["moving_averages"] if ma.signal == TrendType.BULLISH)
        total_mas = len(analysis_data["moving_averages"])
        summary += f"Le prix est au-dessus de {bullish_mas}/{total_mas} moyennes mobiles. "

        # Ajouter le signal
        if signal.action == SignalType.BUY:
            summary += f"Signal d'ACHAT avec {signal.confidence}% de confiance. "
        elif signal.action == SignalType.SELL:
            summary += f"Signal de VENTE avec {signal.confidence}% de confiance. "
        else:
            summary += "Pas de signal clair, il est recommandé d'attendre. "

        summary += f"Ratio Risk/Reward: 1:{signal.risk_reward}"

        return summary

    async def get_quick_signal(self, symbol: str = "BTCUSDT") -> TradingSignal:
        """Obtenir rapidement un signal sans l'analyse complète"""
        analysis = await self.get_full_analysis(symbol)
        return analysis.signal


# Instance singleton
analysis_service = AnalysisService()
