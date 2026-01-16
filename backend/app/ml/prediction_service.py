"""
Service de prédiction LSTM pour BTC - Option B (Classification UP/DOWN)

Ce service charge le modèle LSTM entraîné sur Colab et prédit
si le prix du BTC va monter (UP) ou descendre (DOWN) demain.

============ MODELE OPTION B ============

Le modèle prédit:
- UP (1): Le prix de clôture demain > aujourd'hui
- DOWN (0): Le prix de clôture demain < aujourd'hui

Features utilisées (12):
- Open, High, Low, Close, Volume
- Returns, Returns_2d, Returns_5d
- Volatility, Range, Close_Position, Volume_Ratio

Sequence: 14 jours

============ FICHIERS REQUIS ============

Placez ces fichiers dans backend/app/ml/models/:
1. btc_lstm_model_B.keras  - Le modèle Keras entraîné
2. btc_scaler_B.pkl        - Le normaliseur
3. training_config_B.json  - Configuration et métriques
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Désactiver les warnings TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class BTCPredictionService:
    """
    Service de prédiction du prix BTC utilisant un modèle LSTM Classification.

    Le modèle prédit si le prix va monter (UP) ou descendre (DOWN) demain.
    """

    def __init__(self):
        self.model = None
        self.scalers = None
        self.config = None
        self.is_loaded = False
        self.last_prediction_date: Optional[date] = None
        self.cached_prediction: Optional[Dict] = None

        # Chemins des fichiers - Option B
        self.models_dir = Path(__file__).parent / "models"
        self.model_path = self.models_dir / "btc_lstm_model_B.keras"
        self.scaler_path = self.models_dir / "btc_scaler_B.pkl"
        self.config_path = self.models_dir / "training_config_B.json"

    def load_model(self) -> bool:
        """
        Charge le modèle LSTM et les scalers.

        Returns:
            bool: True si le chargement a réussi
        """
        try:
            # Vérifier que les fichiers existent
            if not self.model_path.exists():
                print(f"Modèle non trouvé: {self.model_path}")
                return False

            if not self.scaler_path.exists():
                print(f"Scalers non trouvés: {self.scaler_path}")
                return False

            # Charger TensorFlow/Keras (import différé pour performance)
            import tensorflow as tf
            from tensorflow import keras

            print("Chargement du modèle LSTM Classification (Option B)...")
            self.model = keras.models.load_model(str(self.model_path))
            print(f"   Modèle chargé: {self.model_path}")

            # Charger les scalers
            self.scalers = joblib.load(str(self.scaler_path))
            print(f"   Scalers chargés: {self.scaler_path}")

            # Charger la configuration
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                print(f"   Config chargée: {self.config_path}")
            else:
                # Configuration par défaut Option B
                self.config = {
                    'sequence_length': 14,
                    'feature_columns': [
                        'Open', 'High', 'Low', 'Close', 'Volume',
                        'Returns', 'Returns_2d', 'Returns_5d',
                        'Volatility', 'Range', 'Close_Position', 'Volume_Ratio'
                    ],
                    'target': 'direction (UP=1, DOWN=0)'
                }

            self.is_loaded = True
            print("Modèle LSTM Classification prêt!")
            return True

        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.is_loaded = False
            return False

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les features pour la classification.

        Doit créer les MÊMES features que celles utilisées lors de l'entraînement.
        """
        df = df.copy()

        # Normalize column names to capitalized format
        df.columns = df.columns.str.capitalize()
        if 'Open' not in df.columns and 'open' in df.columns:
            df = df.rename(columns={col: col.capitalize() for col in df.columns})

        # Returns
        df['Returns'] = df['Close'].pct_change()
        df['Returns_2d'] = df['Close'].pct_change(2)
        df['Returns_5d'] = df['Close'].pct_change(5)

        # Volatilité
        df['Volatility'] = df['Returns'].rolling(window=7).std()

        # Range normalisé
        df['Range'] = (df['High'] - df['Low']) / df['Close']

        # Position dans le range du jour
        df['Close_Position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'] + 1e-8)

        # Volume relatif
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()

        # Remplacer les inf par NaN puis forward fill
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.ffill().bfill()

        return df

    async def predict_tomorrow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Prédit si le prix va monter ou descendre demain.

        Args:
            df: DataFrame avec au moins 14 jours de données OHLCV

        Returns:
            Dict avec la prédiction UP/DOWN et métadonnées
        """
        if not self.is_loaded:
            success = self.load_model()
            if not success:
                raise RuntimeError("Impossible de charger le modèle. Assurez-vous que les fichiers sont présents dans backend/app/ml/models/")

        # Vérifier le cache
        today = date.today()
        if self.last_prediction_date == today and self.cached_prediction:
            return self.cached_prediction

        # Créer les features
        df_features = self.create_features(df)

        # Sélectionner les colonnes de features
        feature_columns = self.config.get('feature_columns', [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'Returns', 'Returns_2d', 'Returns_5d',
            'Volatility', 'Range', 'Close_Position', 'Volume_Ratio'
        ])

        # Filtrer les colonnes existantes
        available_columns = [col for col in feature_columns if col in df_features.columns]

        sequence_length = self.config.get('sequence_length', 14)

        # Prendre les dernières données
        last_data = df_features[available_columns].tail(sequence_length).values

        if len(last_data) < sequence_length:
            raise ValueError(f"Pas assez de données. Requis: {sequence_length}, Disponible: {len(last_data)}")

        # Normaliser
        scaler = self.scalers.get('scaler_features', self.scalers)
        last_data_scaled = scaler.transform(last_data)

        # Reshape pour LSTM: (1, sequence_length, features)
        X = last_data_scaled.reshape(1, sequence_length, -1)

        # Prédire (retourne une probabilité entre 0 et 1)
        prob_up = float(self.model.predict(X, verbose=0)[0][0])
        prob_down = 1.0 - prob_up

        # Déterminer la prédiction
        prediction = "UP" if prob_up > 0.5 else "DOWN"
        confidence = max(prob_up, prob_down) * 100

        # Déterminer la force du signal
        if confidence >= 65:
            signal_strength = "STRONG"
        elif confidence >= 55:
            signal_strength = "MODERATE"
        else:
            signal_strength = "WEAK"

        # Prix actuel (utiliser df_features qui a les colonnes capitalisées)
        current_close = float(df_features['Close'].iloc[-1])

        # Construire la réponse
        prediction_date = today + timedelta(days=1)

        result = {
            "prediction_for": prediction_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "current_price": {
                "close": current_close,
                "date": today.isoformat()
            },
            "prediction": {
                "direction": prediction,
                "confidence": round(confidence, 2),
                "signal_strength": signal_strength,
                "probabilities": {
                    "UP": round(prob_up * 100, 2),
                    "DOWN": round(prob_down * 100, 2)
                }
            },
            "recommendation": self._get_recommendation(prediction, confidence, signal_strength),
            "model_info": {
                "version": self.config.get('model_version', '1.0.0-B'),
                "type": "Classification UP/DOWN",
                "trained_at": self.config.get('trained_at', 'unknown'),
                "sequence_length": sequence_length,
                "metrics": self.config.get('metrics', {})
            }
        }

        # Mettre en cache
        self.last_prediction_date = today
        self.cached_prediction = result

        return result

    def _get_recommendation(self, prediction: str, confidence: float, strength: str) -> Dict[str, str]:
        """Génère une recommandation basée sur la prédiction."""
        if strength == "STRONG":
            if prediction == "UP":
                return {
                    "action": "CONSIDER_BUY",
                    "message": f"Signal haussier fort ({confidence:.1f}%). Le modèle prédit une hausse demain.",
                    "risk_level": "MODERATE"
                }
            else:
                return {
                    "action": "CONSIDER_SELL",
                    "message": f"Signal baissier fort ({confidence:.1f}%). Le modèle prédit une baisse demain.",
                    "risk_level": "MODERATE"
                }
        elif strength == "MODERATE":
            if prediction == "UP":
                return {
                    "action": "WATCH",
                    "message": f"Signal haussier modéré ({confidence:.1f}%). Surveillez les confirmations.",
                    "risk_level": "HIGH"
                }
            else:
                return {
                    "action": "WATCH",
                    "message": f"Signal baissier modéré ({confidence:.1f}%). Surveillez les confirmations.",
                    "risk_level": "HIGH"
                }
        else:
            return {
                "action": "HOLD",
                "message": f"Signal faible ({confidence:.1f}%). Pas de direction claire, attendez un meilleur signal.",
                "risk_level": "HIGH"
            }

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service de prédiction."""
        return {
            "is_loaded": self.is_loaded,
            "model_type": "Classification UP/DOWN (Option B)",
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "scaler_exists": self.scaler_path.exists(),
            "config_exists": self.config_path.exists(),
            "last_prediction_date": self.last_prediction_date.isoformat() if self.last_prediction_date else None,
            "config": self.config if self.is_loaded else None
        }

    def clear_cache(self):
        """Efface le cache des prédictions."""
        self.last_prediction_date = None
        self.cached_prediction = None


# Instance singleton
prediction_service = BTCPredictionService()
