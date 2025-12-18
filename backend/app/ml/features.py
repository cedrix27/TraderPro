"""
Feature Engineering pour le modèle de trading

Ce fichier transforme les données brutes en features utilisables par le ML

============ EXPLICATION DU FEATURE ENGINEERING ============

Le Feature Engineering est l'étape la plus importante du ML.
C'est l'art de transformer les données brutes en informations
que le modèle peut comprendre et utiliser.

Pour le trading, on crée des features basées sur:
1. Prix (variations, ratios)
2. Volume (activité du marché)
3. Indicateurs techniques (RSI, MACD, etc.)
4. Patterns temporels (heure, jour de la semaine)
5. Statistiques rolling (moyennes, écarts-types sur N périodes)
"""
import pandas as pd
import numpy as np
from typing import Tuple
from app.services.indicators_service import IndicatorsService


class FeatureEngineering:
    """
    Classe pour créer les features du modèle ML

    ============ FEATURES CRÉÉES ============

    1. FEATURES DE PRIX
       - returns: Variation en % par rapport à la période précédente
       - log_returns: Log du ratio de prix (plus stable statistiquement)
       - high_low_ratio: Ratio High/Low (volatilité intraday)
       - close_open_ratio: Ratio Close/Open (direction de la bougie)

    2. FEATURES DE VOLUME
       - volume_change: Variation du volume
       - volume_ma_ratio: Volume actuel / Moyenne mobile volume

    3. FEATURES D'INDICATEURS
       - rsi: RSI normalisé (0-1)
       - macd_histogram: MACD histogram normalisé
       - bb_position: Position dans les Bollinger Bands (0-1)
       - ma_distances: Distance du prix aux différentes MAs

    4. FEATURES TEMPORELLES
       - hour: Heure de la journée (0-23)
       - day_of_week: Jour de la semaine (0-6)
       - is_weekend: Booléen weekend

    5. FEATURES STATISTIQUES
       - rolling_mean_X: Moyenne sur X périodes
       - rolling_std_X: Écart-type sur X périodes
       - rolling_min_X: Minimum sur X périodes
       - rolling_max_X: Maximum sur X périodes
    """

    def __init__(self):
        self.indicators = IndicatorsService()

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Créer toutes les features à partir des données OHLCV

        Args:
            df: DataFrame avec colonnes open, high, low, close, volume

        Returns:
            DataFrame avec toutes les features
        """
        features = pd.DataFrame(index=df.index)

        # ========== FEATURES DE PRIX ==========

        # Returns (variation en %)
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Ratios de bougie
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_open_ratio'] = df['close'] / df['open']
        features['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        features['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        features['body_size'] = abs(df['close'] - df['open']) / df['close']

        # ========== FEATURES DE VOLUME ==========

        features['volume_change'] = df['volume'].pct_change()
        features['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()

        # ========== FEATURES D'INDICATEURS ==========

        # RSI
        rsi = self.indicators.calculate_rsi(df)
        features['rsi'] = rsi / 100  # Normaliser entre 0 et 1
        features['rsi_oversold'] = (rsi < 30).astype(int)
        features['rsi_overbought'] = (rsi > 70).astype(int)

        # MACD
        macd_line, signal_line, histogram = self.indicators.calculate_macd(df)
        features['macd_histogram'] = histogram / df['close']  # Normaliser
        features['macd_crossover'] = ((macd_line > signal_line) &
                                       (macd_line.shift(1) <= signal_line.shift(1))).astype(int)
        features['macd_crossunder'] = ((macd_line < signal_line) &
                                        (macd_line.shift(1) >= signal_line.shift(1))).astype(int)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.indicators.calculate_bollinger_bands(df)
        features['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        features['bb_width'] = (bb_upper - bb_lower) / bb_middle

        # Distance aux Moyennes Mobiles (en %)
        for period in [9, 20, 50, 200]:
            if period == 9:
                ma = self.indicators.calculate_ema(df, period)
            else:
                ma = self.indicators.calculate_sma(df, period)
            features[f'ma_{period}_distance'] = (df['close'] - ma) / ma * 100

        # Position relative aux MAs (1 si au-dessus, 0 sinon)
        features['above_ma_20'] = (df['close'] > self.indicators.calculate_sma(df, 20)).astype(int)
        features['above_ma_50'] = (df['close'] > self.indicators.calculate_sma(df, 50)).astype(int)
        features['above_ma_200'] = (df['close'] > self.indicators.calculate_sma(df, 200)).astype(int)

        # ATR (volatilité)
        atr = self.indicators.calculate_atr(df)
        features['atr_ratio'] = atr / df['close']

        # ========== FEATURES TEMPORELLES ==========

        if isinstance(df.index, pd.DatetimeIndex):
            features['hour'] = df.index.hour
            features['day_of_week'] = df.index.dayofweek
            features['is_weekend'] = (df.index.dayofweek >= 5).astype(int)

        # ========== FEATURES STATISTIQUES ROLLING ==========

        for window in [5, 10, 20]:
            # Moyennes
            features[f'returns_mean_{window}'] = features['returns'].rolling(window).mean()
            features[f'returns_std_{window}'] = features['returns'].rolling(window).std()

            # Min/Max
            features[f'price_min_{window}'] = df['low'].rolling(window).min() / df['close']
            features[f'price_max_{window}'] = df['high'].rolling(window).max() / df['close']

            # Momentum
            features[f'momentum_{window}'] = df['close'] / df['close'].shift(window) - 1

        # ========== FEATURES LAGGÉES ==========

        for lag in [1, 2, 3, 5]:
            features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
            features[f'volume_change_lag_{lag}'] = features['volume_change'].shift(lag)

        return features

    def create_target(
        self,
        df: pd.DataFrame,
        horizon: int = 4,
        threshold: float = 0.02
    ) -> pd.Series:
        """
        Créer la variable cible (label) pour l'entraînement

        Args:
            df: DataFrame avec les prix
            horizon: Nombre de périodes pour calculer le futur
            threshold: Seuil de variation pour BUY/SELL (défaut 2%)

        Returns:
            Series avec labels: 1 (BUY), -1 (SELL), 0 (HOLD)

        ============ EXPLICATION DU LABELLING ============

        On labellise les données historiques pour entraîner le modèle:
        - Si le prix monte de plus de X% dans les N prochaines périodes → BUY (1)
        - Si le prix baisse de plus de X% → SELL (-1)
        - Sinon → HOLD (0)

        C'est une forme de "hindsight" - on utilise le futur pour créer les labels
        """
        # Calculer le return futur
        future_return = df['close'].shift(-horizon) / df['close'] - 1

        # Créer les labels
        target = pd.Series(0, index=df.index)  # Default: HOLD
        target[future_return > threshold] = 1   # BUY
        target[future_return < -threshold] = -1  # SELL

        return target

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        horizon: int = 4,
        threshold: float = 0.02
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Préparer les données pour l'entraînement

        Args:
            df: DataFrame OHLCV
            horizon: Horizon de prédiction
            threshold: Seuil pour labelling

        Returns:
            Tuple (features, target) nettoyés
        """
        # Créer features et target
        features = self.create_features(df)
        target = self.create_target(df, horizon, threshold)

        # Supprimer les lignes avec NaN
        valid_idx = features.dropna().index.intersection(target.dropna().index)

        # Ne pas inclure les dernières lignes (pas de target futur)
        valid_idx = valid_idx[:-horizon]

        return features.loc[valid_idx], target.loc[valid_idx]


# Instance singleton
feature_engineering = FeatureEngineering()
