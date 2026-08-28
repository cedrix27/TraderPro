"""
TTM (Tiny Time Mixer) Prediction Service for TraderPro.

Ce service utilise le modèle TTM d'IBM fine-tuné sur les données BTC
pour prédire la direction du prix (UP/DOWN) pour le lendemain.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import joblib


class TTMPredictionService:
    """
    Service de prédiction utilisant le modèle TTM (Tiny Time Mixer).

    TTM est un transformer léger spécialisé pour les séries temporelles,
    pré-entraîné par IBM et fine-tuné sur les données BTC.

    Modèle: ibm-granite/granite-timeseries-ttm-r2
    """

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.config = None
        self.is_loaded = False

        # Cache pour éviter les prédictions redondantes
        self.last_prediction_date: Optional[date] = None
        self.cached_prediction: Optional[Dict] = None

        # Chemins des fichiers
        self.models_dir = Path(__file__).parent / "models" / "ttm"
        self.model_path = self.models_dir
        self.preprocessor_path = self.models_dir / "preprocessor.pkl"
        self.config_path = self.models_dir / "ttm_config.json"

        # Token Hugging Face (optionnel, pour charger depuis HF Hub)
        self.hf_token = "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"

        # Configuration par défaut
        self.default_config = {
            "context_length": 64,
            "forecast_length": 1,
            "feature_columns": [
                "Close", "Open", "High", "Low", "Volume",
                "Returns", "Returns_5d", "Log_returns",
                "Volatility_7d", "Volatility_14d",
                "RSI_norm", "MACD_norm", "BB_position",
                "Price_SMA7_ratio", "Price_SMA20_ratio",
                "Volume_ratio", "ATR_norm", "Daily_range"
            ]
        }

    def load_model(self) -> bool:
        """
        Charge le modèle TTM, le preprocessor et la configuration.

        Returns:
            bool: True si chargement réussi, False sinon
        """
        try:
            # Vérifier que le dossier existe
            if not self.models_dir.exists():
                print(f"[TTM] Dossier modèle non trouvé: {self.models_dir}")
                return False

            # 1. Charger la configuration
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                print(f"[TTM] Configuration chargée: {self.config_path}")
            else:
                print(f"[TTM] Config non trouvée, utilisation des valeurs par défaut")
                self.config = self.default_config

            # 2. Charger le preprocessor
            if self.preprocessor_path.exists():
                self.preprocessor = joblib.load(str(self.preprocessor_path))
                print(f"[TTM] Preprocessor chargé: {self.preprocessor_path}")
            else:
                print(f"[TTM] Preprocessor non trouvé: {self.preprocessor_path}")
                # On peut continuer sans preprocessor, on utilisera une normalisation simple
                self.preprocessor = None

            # 3. Charger le modèle TTM (lazy import pour éviter les erreurs si non installé)
            try:
                from tsfm_public.models.tinytimemixer import TinyTimeMixerForPrediction
                import torch

                self.model = TinyTimeMixerForPrediction.from_pretrained(str(self.model_path))
                self.model.eval()

                # Déplacer sur GPU si disponible
                if torch.cuda.is_available():
                    self.model = self.model.cuda()
                    print("[TTM] Modèle chargé sur GPU")
                else:
                    print("[TTM] Modèle chargé sur CPU")

            except ImportError:
                print("[TTM] ERREUR: tsfm_public n'est pas installé")
                print("[TTM] Installez avec: pip install tsfm_public")
                return False
            except Exception as e:
                print(f"[TTM] Erreur chargement modèle: {e}")
                return False

            self.is_loaded = True
            print("[TTM] Service prêt!")
            return True

        except Exception as e:
            print(f"[TTM] Erreur lors du chargement: {e}")
            self.is_loaded = False
            return False

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les features techniques pour TTM.

        Args:
            df: DataFrame avec colonnes OHLCV

        Returns:
            DataFrame avec les features calculées
        """
        data = df.copy()

        # Normaliser les noms de colonnes
        data.columns = [col.capitalize() for col in data.columns]

        # --- Returns ---
        data['Returns'] = data['Close'].pct_change()
        data['Returns_5d'] = data['Close'].pct_change(5)
        data['Log_returns'] = np.log(data['Close'] / data['Close'].shift(1))

        # --- Volatilité ---
        data['Volatility_7d'] = data['Returns'].rolling(7).std()
        data['Volatility_14d'] = data['Returns'].rolling(14).std()

        # --- RSI ---
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        data['RSI'] = 100 - (100 / (1 + rs))
        data['RSI_norm'] = data['RSI'] / 100

        # --- MACD ---
        ema12 = data['Close'].ewm(span=12).mean()
        ema26 = data['Close'].ewm(span=26).mean()
        data['MACD'] = ema12 - ema26
        data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
        data['MACD_hist'] = data['MACD'] - data['MACD_signal']
        data['MACD_norm'] = data['MACD_hist'] / data['Close'] * 100

        # --- Bollinger Bands ---
        sma20 = data['Close'].rolling(20).mean()
        std20 = data['Close'].rolling(20).std()
        data['BB_upper'] = sma20 + 2 * std20
        data['BB_lower'] = sma20 - 2 * std20
        data['BB_position'] = (data['Close'] - data['BB_lower']) / (data['BB_upper'] - data['BB_lower'] + 1e-10)

        # --- Moving Averages ---
        data['SMA_7'] = data['Close'].rolling(7).mean()
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['Price_SMA7_ratio'] = data['Close'] / data['SMA_7']
        data['Price_SMA20_ratio'] = data['Close'] / data['SMA_20']

        # --- Volume (optionnel - pas toujours disponible) ---
        if 'Volume' in data.columns:
            data['Volume_SMA'] = data['Volume'].rolling(20).mean()
            data['Volume_ratio'] = data['Volume'] / (data['Volume_SMA'] + 1e-10)
        else:
            # Volume non disponible, créer des colonnes factices si nécessaire
            data['Volume'] = 0.0
            data['Volume_SMA'] = 0.0
            data['Volume_ratio'] = 1.0

        # --- ATR ---
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['ATR'] = tr.rolling(14).mean()
        data['ATR_norm'] = data['ATR'] / data['Close']

        # --- Daily Range ---
        data['Daily_range'] = (data['High'] - data['Low']) / data['Close']

        # Nettoyer
        data = data.replace([np.inf, -np.inf], np.nan)
        data = data.ffill().bfill()

        return data

    async def predict_tomorrow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Prédit la direction du prix BTC pour demain.

        Args:
            df: DataFrame avec les données historiques (OHLCV)

        Returns:
            Dict avec la prédiction et les métadonnées
        """
        # Charger le modèle si nécessaire
        if not self.is_loaded:
            success = self.load_model()
            if not success:
                raise RuntimeError(
                    "Impossible de charger le modèle TTM. "
                    "Vérifiez que les fichiers sont dans backend/app/ml/models/ttm/"
                )

        # Vérifier le cache
        today = date.today()
        if self.last_prediction_date == today and self.cached_prediction:
            return self.cached_prediction

        # Créer les features
        df_features = self.create_features(df)

        # Obtenir les colonnes de features
        feature_columns = self.config.get('feature_columns', self.default_config['feature_columns'])
        available_columns = [col for col in feature_columns if col in df_features.columns]

        context_length = self.config.get('context_length', 64)

        # Vérifier qu'on a assez de données
        if len(df_features) < context_length:
            raise ValueError(
                f"Pas assez de données. Requis: {context_length}, Disponible: {len(df_features)}"
            )

        # Préparer les données pour la prédiction
        import torch

        # Prendre les derniers context_length jours
        input_data = df_features[available_columns].tail(context_length).values

        # Normaliser manuellement si pas de preprocessor
        if self.preprocessor is None:
            # Normalisation simple (z-score par feature)
            mean = input_data.mean(axis=0)
            std = input_data.std(axis=0) + 1e-8
            input_data = (input_data - mean) / std

        # Convertir en tensor
        input_tensor = torch.FloatTensor(input_data).unsqueeze(0)  # (1, context_length, n_features)

        # Déplacer sur GPU si nécessaire
        if torch.cuda.is_available() and next(self.model.parameters()).is_cuda:
            input_tensor = input_tensor.cuda()

        # Prédiction
        self.model.eval()
        with torch.no_grad():
            try:
                # TTM attend past_values comme entrée
                outputs = self.model(past_values=input_tensor)
                prediction_raw = outputs.prediction_outputs[0, 0, 0].item()
            except Exception as e:
                # Fallback: essayer avec d'autres noms de paramètres
                try:
                    outputs = self.model(input_tensor)
                    if hasattr(outputs, 'prediction_outputs'):
                        prediction_raw = outputs.prediction_outputs[0, 0, 0].item()
                    else:
                        prediction_raw = outputs[0, 0, 0].item()
                except:
                    raise RuntimeError(f"Erreur lors de la prédiction TTM: {e}")

        # Interpréter la prédiction
        current_price = float(df_features['Close'].iloc[-1])
        direction = "UP" if prediction_raw > 0 else "DOWN"

        # Calculer la confiance (basée sur la magnitude)
        confidence = min(abs(prediction_raw) * 100, 95)

        # Probabilités approximatives
        if direction == "UP":
            prob_up = 50 + confidence / 2
            prob_down = 100 - prob_up
        else:
            prob_down = 50 + confidence / 2
            prob_up = 100 - prob_down

        # Force du signal
        if confidence >= 65:
            signal_strength = "STRONG"
        elif confidence >= 50:
            signal_strength = "MODERATE"
        else:
            signal_strength = "WEAK"

        # Construire la réponse
        prediction_date = today + timedelta(days=1)

        result = {
            "prediction_for": prediction_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "current_price": {
                "close": current_price,
                "date": today.isoformat()
            },
            "prediction": {
                "direction": direction,
                "confidence": round(confidence, 2),
                "signal_strength": signal_strength,
                "raw_value": round(prediction_raw, 6),
                "probabilities": {
                    "UP": round(prob_up, 2),
                    "DOWN": round(prob_down, 2)
                }
            },
            "recommendation": self._get_recommendation(direction, confidence, signal_strength),
            "model_info": {
                "type": "TTM (Tiny Time Mixer)",
                "version": self.config.get('model_version', '1.0.0'),
                "base_model": self.config.get('base_model', 'ibm-granite/granite-timeseries-ttm-v1'),
                "context_length": context_length,
                "trained_at": self.config.get('trained_at', 'unknown'),
                "metrics": self._sanitize_metrics(self.config.get('metrics', {}))
            }
        }

        # Mettre en cache
        self.last_prediction_date = today
        self.cached_prediction = result

        return result

    def _sanitize_metrics(self, metrics: Dict) -> Dict:
        """Nettoie les métriques pour les rendre JSON-compatibles (remplace NaN/Inf)."""
        import math
        sanitized = {}
        for key, value in metrics.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    sanitized[key] = None
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        return sanitized

    def _get_recommendation(self, direction: str, confidence: float, signal_strength: str) -> Dict[str, Any]:
        """Génère une recommandation basée sur la prédiction."""

        if signal_strength == "STRONG":
            if direction == "UP":
                action = "CONSIDER_BUY"
                text = "Signal haussier fort détecté par TTM. Le modèle prédit une hausse avec haute confiance."
            else:
                action = "CONSIDER_SELL"
                text = "Signal baissier fort détecté par TTM. Le modèle prédit une baisse avec haute confiance."
        elif signal_strength == "MODERATE":
            if direction == "UP":
                action = "HOLD_BULLISH"
                text = "Signal haussier modéré. Attendre confirmation avant de prendre position."
            else:
                action = "HOLD_BEARISH"
                text = "Signal baissier modéré. Surveiller l'évolution avant de vendre."
        else:
            action = "WAIT"
            text = "Signal faible. Le modèle n'a pas assez de confiance pour une recommandation claire."

        return {
            "action": action,
            "text": text,
            "confidence_level": signal_strength,
            "disclaimer": "Cette prédiction est générée par un modèle IA et ne constitue pas un conseil financier."
        }

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service TTM."""
        return {
            "service": "TTM (Tiny Time Mixer)",
            "is_loaded": self.is_loaded,
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "preprocessor_exists": self.preprocessor_path.exists(),
            "config_exists": self.config_path.exists(),
            "last_prediction_date": self.last_prediction_date.isoformat() if self.last_prediction_date else None,
            "cache_active": self.cached_prediction is not None,
            "config": self.config if self.is_loaded else None,
            "required_files": [
                "config.json",
                "model.safetensors",
                "preprocessor.pkl",
                "ttm_config.json"
            ]
        }

    def clear_cache(self):
        """Efface le cache des prédictions."""
        self.last_prediction_date = None
        self.cached_prediction = None


# Instance singleton
ttm_prediction_service = TTMPredictionService()
