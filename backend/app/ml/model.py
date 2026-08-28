"""Pipeline XGBoost reproductible pour les signaux BTC de TraderPro."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from itertools import product
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

from app.core.config import settings
from app.ml.features import feature_engineering


LABEL_TO_CLASS = {-1: 0, 0: 1, 1: 2}
CLASS_TO_LABEL = {value: key for key, value in LABEL_TO_CLASS.items()}
LABEL_NAMES = ["SELL", "HOLD", "BUY"]


class TradingModel:
    """Classifieur directionnel BTC avec validation chronologique purgée."""

    def __init__(self) -> None:
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler = StandardScaler()
        self.feature_names: list[str] = []
        self.is_trained = False
        self.metrics: Dict[str, Any] = {}

    @property
    def artifact_path(self) -> Path:
        path = Path(settings.model_path)
        return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path

    @property
    def manifest_path(self) -> Path:
        return self.artifact_path.with_suffix(".manifest.json")

    @staticmethod
    def _split_chronologically(
        X: pd.DataFrame, y: pd.Series, *, horizon: int, validation_size: float, test_size: float
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """Split train/validation/test avec une zone purgée de ``horizon`` bougies."""
        if not 0 < validation_size < 0.3 or not 0 < test_size < 0.3:
            raise ValueError("validation_size et test_size doivent être comprises entre 0 et 0.3.")
        n_rows = len(X)
        validation_rows, test_rows = int(n_rows * validation_size), int(n_rows * test_size)
        train_end = n_rows - validation_rows - test_rows - (2 * horizon)
        validation_start = train_end + horizon
        test_start = validation_start + validation_rows + horizon
        if min(train_end, validation_rows, test_rows) < 300:
            raise ValueError("Pas assez de données pour train/validation/test. Utilisez au moins 5 000 bougies.")
        return (
            X.iloc[:train_end], y.iloc[:train_end],
            X.iloc[validation_start:test_start - horizon], y.iloc[validation_start:test_start - horizon],
            X.iloc[test_start:], y.iloc[test_start:],
        )

    def train(
        self,
        df: pd.DataFrame,
        horizon: int = 4,
        threshold: float = 0.004,
        validation_size: float = 0.15,
        test_size: float = 0.15,
        grid_search: bool = True,
    ) -> Dict[str, Any]:
        """Entraîne sur le passé, règle l'arrêt précoce sur validation, mesure sur test final."""
        if horizon < 1:
            raise ValueError("horizon doit être supérieur ou égal à 1.")
        X, y = feature_engineering.prepare_training_data(df, horizon, threshold)
        if len(X) < 5_000:
            raise ValueError(f"{len(X)} exemples disponibles : 5 000 minimum requis.")
        if set(y.unique()) != {-1, 0, 1}:
            raise ValueError("Les trois classes BUY/HOLD/SELL doivent être présentes. Réduisez le threshold ou augmentez l'historique.")

        self.feature_names = X.columns.tolist()
        X_train, y_train, X_validation, y_validation, X_test, y_test = self._split_chronologically(
            X, y, horizon=horizon, validation_size=validation_size, test_size=test_size
        )
        if set(y_train.unique()) != {-1, 0, 1}:
            raise ValueError("Le jeu d'entraînement ne contient pas les trois classes. Ajustez le threshold.")

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_validation_scaled = self.scaler.transform(X_validation)
        X_test_scaled = self.scaler.transform(X_test)
        y_train_class = y_train.map(LABEL_TO_CLASS)
        y_validation_class = y_validation.map(LABEL_TO_CLASS)
        y_test_class = y_test.map(LABEL_TO_CLASS)

        base_parameters = {
            "learning_rate": 0.03,
            "max_depth": 4,
            "min_child_weight": 8,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.05,
            "reg_lambda": 2.0,
        }
        tuning: Dict[str, Any] = {"enabled": grid_search}
        if grid_search:
            # Le test final reste totalement invisible. Chaque pli CV respecte l'ordre du temps
            # et laisse une zone tampon de ``horizon`` bougies entre apprentissage et validation.
            parameter_grid = {
                "max_depth": [3, 4, 5],
                "min_child_weight": [4, 8],
                "subsample": [0.75, 0.90],
                "colsample_bytree": [0.70, 0.90],
                "reg_alpha": [0.0, 0.05],
                "reg_lambda": [1.0, 3.0],
            }
            candidates = [dict(zip(parameter_grid, values)) for values in product(*parameter_grid.values())]
            cv = TimeSeriesSplit(n_splits=4, gap=horizon)
            results = []
            for candidate_number, candidate in enumerate(candidates, start=1):
                fold_scores = []
                for fold_train, fold_validation in cv.split(X_train):
                    X_fold_train, X_fold_validation = X_train.iloc[fold_train], X_train.iloc[fold_validation]
                    y_fold_train, y_fold_validation = y_train_class.iloc[fold_train], y_train_class.iloc[fold_validation]
                    candidate_model = xgb.XGBClassifier(
                        objective="multi:softprob", num_class=3, n_estimators=500,
                        learning_rate=base_parameters["learning_rate"], eval_metric="mlogloss",
                        # Une seule exécution à la fois : la grille comporte déjà 384 fits.
                        random_state=42, n_jobs=1, tree_method="hist", **candidate,
                    )
                    candidate_model.fit(
                        X_fold_train, y_fold_train,
                        sample_weight=compute_sample_weight(class_weight="balanced", y=y_fold_train),
                        verbose=False,
                    )
                    fold_scores.append(float(f1_score(y_fold_validation, candidate_model.predict(X_fold_validation), average="macro", zero_division=0)))
                results.append({"params": candidate, "mean_cv_macro_f1": float(np.mean(fold_scores))})
                if candidate_number % 12 == 0:
                    print(f"Grid search XGBoost : {candidate_number}/{len(candidates)} candidats évalués")
            results.sort(key=lambda result: result["mean_cv_macro_f1"], reverse=True)
            base_parameters.update(results[0]["params"])
            tuning.update({
                "cv_splits": 4,
                "scoring": "f1_macro",
                "candidates": len(candidates),
                "best_cv_macro_f1": results[0]["mean_cv_macro_f1"],
                "best_params": results[0]["params"],
                "top_candidates": results[:5],
            })

        self.model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=1_200,
            **base_parameters,
            eval_metric="mlogloss",
            early_stopping_rounds=60,
            random_state=42,
            n_jobs=-1,
            tree_method="hist",
        )
        self.model.fit(
            X_train_scaled,
            y_train_class,
            sample_weight=compute_sample_weight(class_weight="balanced", y=y_train_class),
            eval_set=[(X_validation_scaled, y_validation_class)],
            verbose=False,
        )

        predicted_classes = self.model.predict(X_test_scaled).astype(int)
        y_pred = pd.Series(predicted_classes).map(CLASS_TO_LABEL).to_numpy()
        report = classification_report(y_test, y_pred, labels=[-1, 0, 1], target_names=LABEL_NAMES, output_dict=True, zero_division=0)
        importance = pd.DataFrame({"feature": self.feature_names, "importance": self.model.feature_importances_}).sort_values("importance", ascending=False)
        best_iteration = int(getattr(self.model, "best_iteration", self.model.n_estimators))
        self.metrics = {
            "schema_version": 2,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "horizon_candles": horizon,
            "threshold": threshold,
            "source_rows": int(len(df)),
            "feature_count": len(self.feature_names),
            "splits": {
                "train": int(len(X_train)), "validation": int(len(X_validation)), "test": int(len(X_test)), "purge_gap_candles": horizon,
                "train_end": str(X_train.index[-1]), "validation_start": str(X_validation.index[0]), "test_start": str(X_test.index[0]),
            },
            "class_distribution": {name: int((y_train == label).sum()) for name, label in (("SELL", -1), ("HOLD", 0), ("BUY", 1))},
            "test_metrics": {
                "accuracy": float(report["accuracy"]),
                "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
                "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
                "classification_report": report,
                "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[-1, 0, 1]).tolist(),
            },
            "best_iteration": best_iteration,
            "hyperparameter_search": tuning,
            "top_features": importance.head(15).to_dict("records"),
        }
        # Compatibilité avec l'UI et les anciennes réponses API.
        self.metrics["accuracy"] = self.metrics["test_metrics"]["accuracy"]
        self.metrics["classification_report"] = report
        self.metrics["train_size"] = len(X_train)
        self.metrics["test_size"] = len(X_test)
        self.is_trained = True
        return self.metrics

    def predict(self, df: pd.DataFrame) -> Tuple[int, float, Dict[str, float]]:
        if not self.is_trained or self.model is None:
            raise ValueError("Le modèle n'est pas entraîné. Appelez train() d'abord.")
        features = feature_engineering.create_features(df)
        missing = set(self.feature_names) - set(features.columns)
        if missing:
            raise ValueError(f"Features manquantes pour la prédiction : {sorted(missing)}")
        X = features[self.feature_names].iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
        probabilities = self.model.predict_proba(self.scaler.transform(X))[0]
        predicted_class = int(np.argmax(probabilities))
        return CLASS_TO_LABEL[predicted_class], float(probabilities[predicted_class] * 100), {
            "SELL": float(probabilities[0] * 100), "HOLD": float(probabilities[1] * 100), "BUY": float(probabilities[2] * 100),
        }

    def save(self, path: Optional[str] = None) -> Path:
        if not self.is_trained or self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")
        artifact = Path(path) if path else self.artifact_path
        artifact.parent.mkdir(parents=True, exist_ok=True)
        payload = {"model": self.model, "scaler": self.scaler, "feature_names": self.feature_names, "metrics": self.metrics}
        temporary = artifact.with_suffix(artifact.suffix + ".tmp")
        joblib.dump(payload, temporary)
        temporary.replace(artifact)
        if artifact == self.artifact_path:
            self.manifest_path.write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        return artifact

    def load(self, path: Optional[str] = None) -> None:
        artifact = Path(path) if path else self.artifact_path
        if not artifact.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {artifact}")
        payload = joblib.load(artifact)
        self.model, self.scaler = payload["model"], payload["scaler"]
        self.feature_names, self.metrics = payload["feature_names"], payload["metrics"]
        self.is_trained = True

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        if not self.is_trained or self.model is None:
            raise ValueError("Le modèle n'est pas entraîné")
        return pd.DataFrame({"feature": self.feature_names, "importance": self.model.feature_importances_}).sort_values("importance", ascending=False).head(top_n)


trading_model = TradingModel()
