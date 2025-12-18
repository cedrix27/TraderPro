"""
Service de calcul des indicateurs techniques
Utilise pandas-ta pour les calculs d'indicateurs

Ce fichier explique chaque indicateur et comment l'interpréter
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from app.core.models import Indicator, MovingAverage, SupportResistance, TrendType, StrengthLevel


class IndicatorsService:
    """
    Service pour calculer les indicateurs techniques

    ============ GUIDE DES INDICATEURS ============

    1. RSI (Relative Strength Index) - Momentum
       - Mesure la vitesse et le changement des mouvements de prix
       - Valeur: 0-100
       - < 30 = Survendu (signal d'achat potentiel)
       - > 70 = Suracheté (signal de vente potentiel)
       - 30-70 = Zone neutre

    2. MACD (Moving Average Convergence Divergence) - Tendance/Momentum
       - Montre la relation entre deux moyennes mobiles
       - Signal haussier: MACD croise au-dessus de la ligne de signal
       - Signal baissier: MACD croise en-dessous de la ligne de signal

    3. Bollinger Bands - Volatilité
       - Bandes autour d'une moyenne mobile
       - Prix près de la bande supérieure = potentiellement suracheté
       - Prix près de la bande inférieure = potentiellement survendu
       - Resserrement des bandes = breakout imminent

    4. Moyennes Mobiles (SMA/EMA) - Tendance
       - SMA: Simple Moving Average (moyenne simple)
       - EMA: Exponential Moving Average (plus réactive)
       - Prix > MA = tendance haussière
       - Prix < MA = tendance baissière
       - Golden Cross (MA50 > MA200) = très haussier
       - Death Cross (MA50 < MA200) = très baissier

    5. ATR (Average True Range) - Volatilité
       - Mesure la volatilité du marché
       - Utilisé pour calculer les stop-loss dynamiques

    6. Volume - Confirmation
       - Volume élevé confirme le mouvement de prix
       - Volume faible = mouvement potentiellement faible
    """

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculer le RSI (Relative Strength Index)

        Formule:
        RSI = 100 - (100 / (1 + RS))
        RS = Moyenne des gains / Moyenne des pertes
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculer le MACD

        Returns:
            Tuple (macd_line, signal_line, histogram)
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculer les Bollinger Bands

        Returns:
            Tuple (upper_band, middle_band, lower_band)
        """
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculer la Simple Moving Average"""
        return df['close'].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculer l'Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculer l'ATR (Average True Range)

        Mesure de la volatilité
        """
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    @staticmethod
    def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculer la moyenne mobile du volume"""
        return df['volume'].rolling(window=period).mean()

    @staticmethod
    def find_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
        num_levels: int = 3
    ) -> List[SupportResistance]:
        """
        Identifier les niveaux de support et résistance

        Méthode: Trouver les pivots locaux (plus hauts/bas locaux)
        """
        levels = []
        current_price = df['close'].iloc[-1]

        # Trouver les pivots hauts (résistances potentielles)
        df['pivot_high'] = df['high'].rolling(window=window, center=True).max()
        pivot_highs = df[df['high'] == df['pivot_high']]['high'].unique()

        # Trouver les pivots bas (supports potentiels)
        df['pivot_low'] = df['low'].rolling(window=window, center=True).min()
        pivot_lows = df[df['low'] == df['pivot_low']]['low'].unique()

        # Filtrer les résistances (au-dessus du prix actuel)
        resistances = sorted([p for p in pivot_highs if p > current_price])[:num_levels]
        for i, price in enumerate(resistances):
            strength = StrengthLevel.STRONG if i == 0 else (
                StrengthLevel.MEDIUM if i == 1 else StrengthLevel.WEAK
            )
            levels.append(SupportResistance(
                type="resistance",
                price=float(price),
                strength=strength,
                touches=int(np.sum(np.abs(df['high'] - price) / price < 0.005))
            ))

        # Filtrer les supports (en-dessous du prix actuel)
        supports = sorted([p for p in pivot_lows if p < current_price], reverse=True)[:num_levels]
        for i, price in enumerate(supports):
            strength = StrengthLevel.STRONG if i == 0 else (
                StrengthLevel.MEDIUM if i == 1 else StrengthLevel.WEAK
            )
            levels.append(SupportResistance(
                type="support",
                price=float(price),
                strength=strength,
                touches=int(np.sum(np.abs(df['low'] - price) / price < 0.005))
            ))

        return levels

    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculer tous les indicateurs pour un DataFrame

        Args:
            df: DataFrame avec colonnes open, high, low, close, volume

        Returns:
            Dict avec tous les indicateurs calculés
        """
        current_price = df['close'].iloc[-1]

        # RSI
        rsi = self.calculate_rsi(df)
        rsi_value = rsi.iloc[-1]
        rsi_signal = (
            TrendType.BEARISH if rsi_value > 70 else
            TrendType.BULLISH if rsi_value < 30 else
            TrendType.NEUTRAL
        )

        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(df)
        macd_value = macd_line.iloc[-1]
        macd_signal = TrendType.BULLISH if histogram.iloc[-1] > 0 else TrendType.BEARISH

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df)
        bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        bb_signal = (
            TrendType.BEARISH if bb_position > 0.8 else
            TrendType.BULLISH if bb_position < 0.2 else
            TrendType.NEUTRAL
        )

        # Moyennes Mobiles
        sma_20 = self.calculate_sma(df, 20)
        sma_50 = self.calculate_sma(df, 50)
        sma_200 = self.calculate_sma(df, 200)
        ema_9 = self.calculate_ema(df, 9)

        # ATR
        atr = self.calculate_atr(df)
        atr_value = atr.iloc[-1]

        # Volume
        volume_sma = self.calculate_volume_sma(df)
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1
        volume_signal = TrendType.BULLISH if volume_ratio > 1.2 else TrendType.NEUTRAL

        # Support/Résistance
        sr_levels = self.find_support_resistance(df)

        # Construire la liste d'indicateurs
        indicators = [
            Indicator(
                name="RSI",
                value=round(rsi_value, 2),
                signal=rsi_signal,
                description=f"RSI à {rsi_value:.1f} - {'Suracheté' if rsi_value > 70 else 'Survendu' if rsi_value < 30 else 'Zone neutre'}"
            ),
            Indicator(
                name="MACD",
                value=round(macd_value, 2),
                signal=macd_signal,
                description=f"MACD {'positif' if macd_value > 0 else 'négatif'}, histogramme {'croissant' if histogram.iloc[-1] > histogram.iloc[-2] else 'décroissant'}"
            ),
            Indicator(
                name="BB",
                value=round(bb_position, 2),
                signal=bb_signal,
                description=f"Prix à {bb_position*100:.0f}% des Bollinger Bands"
            ),
            Indicator(
                name="Volume",
                value=round(volume_ratio * 100, 0),
                signal=volume_signal,
                description=f"Volume {volume_ratio*100:.0f}% de la moyenne"
            ),
            Indicator(
                name="ATR",
                value=round(atr_value, 2),
                signal=TrendType.NEUTRAL,
                description=f"Volatilité ATR: ${atr_value:.2f}"
            ),
        ]

        # Moyennes mobiles
        moving_averages = [
            MovingAverage(
                name="EMA 9",
                period=9,
                value=round(ema_9.iloc[-1], 2),
                signal=TrendType.BULLISH if current_price > ema_9.iloc[-1] else TrendType.BEARISH
            ),
            MovingAverage(
                name="SMA 20",
                period=20,
                value=round(sma_20.iloc[-1], 2),
                signal=TrendType.BULLISH if current_price > sma_20.iloc[-1] else TrendType.BEARISH
            ),
            MovingAverage(
                name="SMA 50",
                period=50,
                value=round(sma_50.iloc[-1], 2),
                signal=TrendType.BULLISH if current_price > sma_50.iloc[-1] else TrendType.BEARISH
            ),
            MovingAverage(
                name="SMA 200",
                period=200,
                value=round(sma_200.iloc[-1], 2),
                signal=TrendType.BULLISH if current_price > sma_200.iloc[-1] else TrendType.BEARISH
            ),
        ]

        # Déterminer la tendance globale
        bullish_count = sum(1 for i in indicators if i.signal == TrendType.BULLISH)
        bullish_count += sum(1 for ma in moving_averages if ma.signal == TrendType.BULLISH)
        bearish_count = sum(1 for i in indicators if i.signal == TrendType.BEARISH)
        bearish_count += sum(1 for ma in moving_averages if ma.signal == TrendType.BEARISH)
        total = bullish_count + bearish_count

        if total > 0:
            trend_strength = abs(bullish_count - bearish_count) / total * 100
        else:
            trend_strength = 0

        trend = (
            TrendType.BULLISH if bullish_count > bearish_count else
            TrendType.BEARISH if bearish_count > bullish_count else
            TrendType.NEUTRAL
        )

        return {
            "indicators": indicators,
            "moving_averages": moving_averages,
            "support_resistance": sr_levels,
            "trend": trend,
            "trend_strength": trend_strength,
            "current_price": current_price,
            "atr": atr_value,
            "raw": {
                "rsi": rsi,
                "macd": macd_line,
                "macd_signal": signal_line,
                "macd_histogram": histogram,
                "bb_upper": bb_upper,
                "bb_middle": bb_middle,
                "bb_lower": bb_lower,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "ema_9": ema_9,
                "atr": atr,
                "volume_sma": volume_sma
            }
        }


# Instance singleton
indicators_service = IndicatorsService()
