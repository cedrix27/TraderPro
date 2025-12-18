"""
Modèle de Machine Learning pour la prédiction de trading

============ ARCHITECTURE DU MODÈLE ============

Ce fichier implémente un modèle de classification pour prédire:
- BUY (1): Le prix va probablement monter
- HOLD (0): Pas de signal clair
- SELL (-1): Le prix va probablement baisser

On utilise XGBoost car:
1. Performant sur les données tabulaires
2. Gère bien les features numériques
3. Rapide à entraîner et à inférer
4. Interprétable (feature importance)

============ PIPELINE D'ENTRAÎNEMENT ============

1. Collecte des données historiques (Binance)
2. Feature Engineering (création des variables)
3. Labelling (création des targets)
4. Split train/test (validation temporelle)
5. Entraînement du modèle
6. Évaluation et validation
7. Sauvegarde du modèle

============ MÉTRIQUES IMPORTANTES ============

Pour le trading, on s'intéresse à:
- Precision: Quand on prédit BUY, est-ce vraiment un bon moment?
- Recall: Capte-t-on toutes les bonnes opportunités?
- F1-Score: Balance precision/recall
- Profit Factor: Gains / Pertes (backtesting)
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import joblib
import os
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

from app.core.config import settings
from app.ml.features import feature_engineering


class TradingModel:
    """
    Modèle XGBoost pour la prédiction de signaux de trading

    ============ UTILISATION ============

    # Entraînement
    model = TradingModel()
    model.train(df_historical)
    model.save()

    # Prédiction
    model = TradingModel()
    model.load()
    signal = model.predict(df_current)
    """

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler = StandardScaler()
        self.feature_names: list = []
        self.is_trained = False
        self.metrics: Dict[str, Any] = {}

    def train(
        self,
        df: pd.DataFrame,
        horizon: int = 4,
        threshold: float = 0.02,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Entraîner le modèle sur les données historiques

        Args:
            df: DataFrame OHLCV
            horizon: Horizon de prédiction (nombre de périodes)
            threshold: Seuil de variation pour labelling
            test_size: Proportion des données pour le test

        Returns:
            Dict avec les métriques d'entraînement

        ============ PROCESSUS D'ENTRAÎNEMENT ============

        1. Préparation des données
        2. Split temporel (important: pas de data leakage!)
        3. Normalisation des features
        4. Entraînement XGBoost
        5. Évaluation sur données de test
        """
        print("🚀 Début de l'entraînement...")

        # 1. Préparer les données
        print("📊 Préparation des features...")
        X, y = feature_engineering.prepare_training_data(df, horizon, threshold)

        self.feature_names = X.columns.tolist()
        print(f"   - {len(self.feature_names)} features créées")
        print(f"   - {len(X)} échantillons")

        # Distribution des classes
        class_dist = y.value_counts()
        print(f"   - Distribution: BUY={class_dist.get(1, 0)}, HOLD={class_dist.get(0, 0)}, SELL={class_dist.get(-1, 0)}")

        # 2. Split temporel (les dernières données pour le test)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        print(f"📈 Split: {len(X_train)} train, {len(X_test)} test")

        # 3. Normalisation
        print("🔄 Normalisation des features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 4. Configuration et entraînement XGBoost
        print("🤖 Entraînement du modèle XGBoost...")

        # Paramètres optimisés pour le trading
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1,
            objective='multi:softmax',
            num_class=3,
            eval_metric='mlogloss',
            use_label_encoder=False,
            random_state=42,
            n_jobs=-1
        )

        # Mapper les labels pour XGBoost (doit être 0, 1, 2)
        label_map = {-1: 0, 0: 1, 1: 2}
        y_train_mapped = y_train.map(label_map)
        y_test_mapped = y_test.map(label_map)

        self.model.fit(
            X_train_scaled, y_train_mapped,
            eval_set=[(X_test_scaled, y_test_mapped)],
            verbose=False
        )

        # 5. Évaluation
        print("📊 Évaluation du modèle...")
        y_pred_mapped = self.model.predict(X_test_scaled)

        # Remapper vers les labels originaux
        reverse_map = {0: -1, 1: 0, 2: 1}
        y_pred = pd.Series(y_pred_mapped).map(reverse_map)
        y_test_original = y_test.reset_index(drop=True)

        # Métriques
        report = classification_report(
            y_test_original, y_pred,
            target_names=['SELL', 'HOLD', 'BUY'],
            output_dict=True
        )

        # Feature importance
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        self.metrics = {
            'classification_report': report,
            'accuracy': report['accuracy'],
            'top_features': importance.head(10).to_dict('records'),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'horizon': horizon,
            'threshold': threshold,
            'trained_at': datetime.now().isoformat()
        }

        self.is_trained = True

        print(f"✅ Entraînement terminé!")
        print(f"   - Accuracy: {report['accuracy']:.2%}")
        print(f"   - Top 3 features: {', '.join(importance['feature'].head(3))}")

        return self.metrics

    def predict(self, df: pd.DataFrame) -> Tuple[int, float, Dict]:
        """
        Prédire le signal pour les données actuelles

        Args:
            df: DataFrame OHLCV récent

        Returns:
            Tuple (signal, confidence, probabilities)
            - signal: 1 (BUY), 0 (HOLD), -1 (SELL)
            - confidence: Probabilité de la prédiction
            - probabilities: Dict avec toutes les probabilités

        ============ PROCESSUS DE PRÉDICTION ============

        1. Créer les features à partir des données actuelles
        2. Normaliser avec le même scaler que l'entraînement
        3. Faire la prédiction
        4. Calculer la confiance
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez train() d'abord.")

        # Créer les features
        features = feature_engineering.create_features(df)

        # Prendre la dernière ligne (données les plus récentes)
        X = features[self.feature_names].iloc[[-1]]

        # Vérifier les NaN
        if X.isna().any().any():
            # Remplacer les NaN par la médiane ou 0
            X = X.fillna(0)

        # Normaliser
        X_scaled = self.scaler.transform(X)

        # Prédire
        pred_mapped = self.model.predict(X_scaled)[0]
        proba = self.model.predict_proba(X_scaled)[0]

        # Remapper
        reverse_map = {0: -1, 1: 0, 2: 1}
        signal = reverse_map[pred_mapped]
        confidence = max(proba) * 100

        probabilities = {
            'SELL': proba[0] * 100,
            'HOLD': proba[1] * 100,
            'BUY': proba[2] * 100
        }

        return signal, confidence, probabilities

    def save(self, path: Optional[str] = None):
        """Sauvegarder le modèle"""
        if not self.is_trained:
            raise ValueError("Aucun modèle à sauvegarder")

        path = path or settings.model_path

        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Sauvegarder le modèle et le scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'metrics': self.metrics
        }

        joblib.dump(model_data, path)
        print(f"✅ Modèle sauvegardé: {path}")

    def load(self, path: Optional[str] = None):
        """Charger un modèle sauvegardé"""
        path = path or settings.model_path

        if not os.path.exists(path):
            raise FileNotFoundError(f"Modèle non trouvé: {path}")

        model_data = joblib.load(path)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.metrics = model_data['metrics']
        self.is_trained = True

        print(f"✅ Modèle chargé: {path}")
        print(f"   - Accuracy: {self.metrics.get('accuracy', 'N/A'):.2%}")

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Obtenir l'importance des features"""
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance.head(top_n)


# Instance singleton
trading_model = TradingModel()
