"""Modèle BTC V2 : rendement attendu, labels dynamiques et exécution coût-aware."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, mean_absolute_error

from app.ml.features import feature_engineering


LABEL_TO_CLASS = {-1: 0, 0: 1, 1: 2}
CLASS_TO_LABEL = {0: -1, 1: 0, 2: 1}


class TradingModelV2:
    """Deux modèles complémentaires : rendement attendu et qualité du signal à barrières ATR."""

    def __init__(self) -> None:
        self.return_model: Optional[xgb.XGBRegressor] = None
        self.direction_model: Optional[xgb.XGBClassifier] = None
        self.confidence_calibrator: Optional[IsotonicRegression] = None
        self.feature_names: list[str] = []
        self.metrics: Dict[str, Any] = {}
        self.is_trained = False
        self.horizon = 12
        self.round_trip_cost = 0.0012
        self.min_confidence = 0.55
        self.min_edge = 0.0015

    @property
    def artifact_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "models/trading_model_v2.joblib"

    @property
    def manifest_path(self) -> Path:
        return self.artifact_path.with_suffix(".manifest.json")

    @staticmethod
    def _dynamic_labels(frame: pd.DataFrame, horizon: int, atr_multiplier: float) -> pd.Series:
        """Triple-barrier simplifié : la première barrière ATR touchée définit LONG/SHORT/HOLD."""
        atr_ratio = feature_engineering.indicators.calculate_atr(frame) / frame["close"]
        labels = pd.Series(0, index=frame.index, dtype="int8")
        closes, highs, lows = frame["close"].to_numpy(), frame["high"].to_numpy(), frame["low"].to_numpy()
        for index in range(len(frame) - horizon):
            barrier = atr_ratio.iloc[index] * atr_multiplier
            if not np.isfinite(barrier) or barrier <= 0:
                continue
            upper, lower = closes[index] * (1 + barrier), closes[index] * (1 - barrier)
            future_high, future_low = highs[index + 1:index + horizon + 1], lows[index + 1:index + horizon + 1]
            upper_hits = np.flatnonzero(future_high >= upper)
            lower_hits = np.flatnonzero(future_low <= lower)
            if len(upper_hits) and (not len(lower_hits) or upper_hits[0] < lower_hits[0]):
                labels.iloc[index] = 1
            elif len(lower_hits) and (not len(upper_hits) or lower_hits[0] < upper_hits[0]):
                labels.iloc[index] = -1
        return labels

    def _dataset(self, df: pd.DataFrame, horizon: int, atr_multiplier: float) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        features = feature_engineering.create_features(df).replace([np.inf, -np.inf], np.nan)
        # Régression sur le rendement logarithmique : plus stable que le prix absolu.
        future_return = np.log(df["close"].shift(-horizon) / df["close"])
        labels = self._dynamic_labels(df, horizon, atr_multiplier)
        valid = features.dropna().index.intersection(future_return.dropna().index)[:-horizon]
        return features.loc[valid], future_return.loc[valid], labels.loc[valid]

    @staticmethod
    def _split(X: pd.DataFrame, returns: pd.Series, labels: pd.Series, horizon: int):
        n = len(X)
        test_rows, validation_rows = int(n * 0.15), int(n * 0.15)
        train_end = n - test_rows - validation_rows - 2 * horizon
        validation_start, test_start = train_end + horizon, train_end + horizon + validation_rows + horizon
        if train_end < 5_000:
            raise ValueError("Historique insuffisant : il faut au moins 5 000 observations après le découpage.")
        return (
            X.iloc[:train_end], returns.iloc[:train_end], labels.iloc[:train_end],
            X.iloc[validation_start:test_start - horizon], returns.iloc[validation_start:test_start - horizon], labels.iloc[validation_start:test_start - horizon],
            X.iloc[test_start:], returns.iloc[test_start:], labels.iloc[test_start:],
        )

    @staticmethod
    def _models() -> tuple[xgb.XGBRegressor, xgb.XGBClassifier]:
        common = dict(n_estimators=1_200, learning_rate=0.025, max_depth=4, min_child_weight=8,
                      subsample=0.8, colsample_bytree=0.9, reg_alpha=0.05, reg_lambda=3.0,
                      random_state=42, n_jobs=-1, tree_method="hist")
        return (
            xgb.XGBRegressor(objective="reg:squarederror", eval_metric="mae", early_stopping_rounds=60, **common),
            xgb.XGBClassifier(objective="multi:softprob", num_class=3, eval_metric="mlogloss", early_stopping_rounds=60, **common),
        )

    def _fit(self, X_train, returns_train, labels_train, X_validation, returns_validation, labels_validation) -> None:
        self.return_model, self.direction_model = self._models()
        self.return_model.fit(X_train, returns_train, eval_set=[(X_validation, returns_validation)], verbose=False)
        class_weights = np.array([len(labels_train) / (3 * max((labels_train == label).sum(), 1)) for label in labels_train])
        self.direction_model.fit(X_train, labels_train.map(LABEL_TO_CLASS), sample_weight=class_weights,
                                 eval_set=[(X_validation, labels_validation.map(LABEL_TO_CLASS))], verbose=False)
        validation_probabilities = self.direction_model.predict_proba(X_validation)
        validation_predictions = np.argmax(validation_probabilities, axis=1)
        success = (validation_predictions == labels_validation.map(LABEL_TO_CLASS).to_numpy()).astype(int)
        self.confidence_calibrator = IsotonicRegression(out_of_bounds="clip")
        self.confidence_calibrator.fit(validation_probabilities.max(axis=1), success)
        self._select_execution_filter(X_validation, returns_validation)

    def _signals(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self.return_model or not self.direction_model or not self.confidence_calibrator:
            raise ValueError("Modèle V2 non entraîné.")
        predicted_returns = self.return_model.predict(X)
        probabilities = self.direction_model.predict_proba(X)
        direction = np.vectorize(CLASS_TO_LABEL.get)(np.argmax(probabilities, axis=1))
        confidence = self.confidence_calibrator.predict(probabilities.max(axis=1))
        return predicted_returns, direction, confidence

    def _select_execution_filter(self, X_validation: pd.DataFrame, returns_validation: pd.Series) -> None:
        """Choisit les seuils sur validation uniquement, en tenant compte des coûts."""
        expected, directions, confidences = self._signals(X_validation)
        candidates = []
        for confidence in (0.35, 0.40, 0.45, 0.50, 0.55):
            for edge in (0.0, 0.0002, 0.0005, 0.0010):
                result = self._backtest(expected, directions, confidences, returns_validation.to_numpy(), confidence=confidence, edge=edge)
                if result["trades"] >= 5:
                    # Rendement net pénalisé par drawdown : le score ne récompense pas le levier caché.
                    candidates.append((result["net_return"] - 0.5 * result["max_drawdown"], confidence, edge))
        if candidates:
            _, self.min_confidence, self.min_edge = max(candidates, key=lambda item: item[0])

    def _backtest(self, predicted_returns: np.ndarray, directions: np.ndarray, confidences: np.ndarray, realized_returns: np.ndarray,
                  *, confidence: Optional[float] = None, edge: Optional[float] = None) -> Dict[str, Any]:
        confidence = self.min_confidence if confidence is None else confidence
        edge = self.min_edge if edge is None else edge
        equities, trade_returns, index = [1.0], [], 0
        while index < len(realized_returns):
            expected = predicted_returns[index]
            side = int(np.sign(expected))
            should_trade = side != 0 and side == int(directions[index]) and confidences[index] >= confidence and abs(expected) >= self.round_trip_cost + edge
            if should_trade:
                net_return = side * (np.exp(realized_returns[index]) - 1) - self.round_trip_cost
                trade_returns.append(net_return)
                equities.append(equities[-1] * (1 + net_return))
                index += self.horizon
            else:
                equities.append(equities[-1])
                index += 1
        curve = np.asarray(equities)
        drawdown = 1 - curve / np.maximum.accumulate(curve)
        winners = [item for item in trade_returns if item > 0]
        losers = [item for item in trade_returns if item < 0]
        profit_factor = (sum(winners) / abs(sum(losers))) if losers else (float("inf") if winners else 0.0)
        sharpe = 0.0 if len(trade_returns) < 2 else float(np.mean(trade_returns) / (np.std(trade_returns) + 1e-12) * np.sqrt(365 * 24 / self.horizon))
        return {"trades": len(trade_returns), "net_return": float(curve[-1] - 1), "sharpe": sharpe,
                "max_drawdown": float(drawdown.max()), "profit_factor": float(profit_factor),
                "win_rate": float(len(winners) / len(trade_returns)) if trade_returns else 0.0}

    def walk_forward_backtest(self, df: pd.DataFrame, horizon: int = 12, atr_multiplier: float = 1.5,
                              train_window: int = 26_280, validation_window: int = 720, test_window: int = 720,
                              start_fold: int = 0, max_folds: Optional[int] = None) -> Dict[str, Any]:
        """Walk-forward mensuel roulant, conçu pour la recherche et jamais pour ajuster le test final."""
        X, returns, labels = self._dataset(df, horizon, atr_multiplier)
        folds, all_trade_returns = [], []
        start, fold_number = 0, 0
        while start + train_window + validation_window + test_window + 2 * horizon <= len(X):
            if max_folds is not None and fold_number >= start_fold + max_folds:
                break
            if fold_number < start_fold:
                start += test_window
                fold_number += 1
                continue
            train_end = start + train_window
            validation_start, validation_end = train_end + horizon, train_end + horizon + validation_window
            test_start, test_end = validation_end + horizon, validation_end + horizon + test_window
            X_train, y_train, l_train = X.iloc[start:train_end], returns.iloc[start:train_end], labels.iloc[start:train_end]
            X_val, y_val, l_val = X.iloc[validation_start:validation_end], returns.iloc[validation_start:validation_end], labels.iloc[validation_start:validation_end]
            X_test, y_test, l_test = X.iloc[test_start:test_end], returns.iloc[test_start:test_end], labels.iloc[test_start:test_end]
            self._fit(X_train, y_train, l_train, X_val, y_val, l_val)
            expected, directions, confidences = self._signals(X_test)
            result = self._backtest(expected, directions, confidences, y_test.to_numpy())
            folds.append({"test_start": str(X_test.index[0]), "test_end": str(X_test.index[-1]), "min_confidence": self.min_confidence, "min_edge": self.min_edge, **result})
            # Réplique les rendements exécutés pour les statistiques agrégées, sans chevauchement des horizons.
            cursor = 0
            while cursor < len(y_test):
                side = int(np.sign(expected[cursor]))
                if side and side == int(directions[cursor]) and confidences[cursor] >= self.min_confidence and abs(expected[cursor]) >= self.round_trip_cost + self.min_edge:
                    all_trade_returns.append(side * (np.exp(y_test.iloc[cursor]) - 1) - self.round_trip_cost)
                    cursor += horizon
                else:
                    cursor += 1
            print(f"Walk-forward V2 : fold {fold_number + 1} — {result['trades']} trades, rendement net {result['net_return']:.2%}", flush=True)
            start += test_window
            fold_number += 1

        equity = np.cumprod(np.r_[1.0, 1.0 + np.asarray(all_trade_returns)])
        drawdown = 1 - equity / np.maximum.accumulate(equity)
        winners, losers = [item for item in all_trade_returns if item > 0], [item for item in all_trade_returns if item < 0]
        return {
            "method": "rolling_3y_train__30d_validation__30d_test",
            "folds": folds,
            "aggregate": {
                "fold_count": len(folds), "trades": len(all_trade_returns), "net_return": float(equity[-1] - 1),
                "max_drawdown": float(drawdown.max()),
                "win_rate": float(len(winners) / len(all_trade_returns)) if all_trade_returns else 0.0,
                "profit_factor": float(sum(winners) / abs(sum(losers))) if losers else 0.0,
            },
        }

    def train(self, df: pd.DataFrame, horizon: int = 12, atr_multiplier: float = 1.5) -> Dict[str, Any]:
        if len(df) < 20_000:
            raise ValueError(f"{len(df)} bougies : 20 000 minimum requis pour le modèle V2.")
        self.horizon = horizon
        X, future_returns, labels = self._dataset(df, horizon, atr_multiplier)
        self.feature_names = X.columns.tolist()
        X_train, y_train, l_train, X_val, y_val, l_val, X_test, y_test, l_test = self._split(X, future_returns, labels, horizon)
        self._fit(X_train, y_train, l_train, X_val, y_val, l_val)
        predicted_returns, directions, confidences = self._signals(X_test)
        predicted_labels = np.vectorize(CLASS_TO_LABEL.get)(self.direction_model.predict(X_test).astype(int))
        backtest = self._backtest(predicted_returns, directions, confidences, y_test.to_numpy())
        self.metrics = {
            "schema_version": 3, "trained_at": datetime.now(timezone.utc).isoformat(), "symbol": "BTCUSDT", "timeframe": "1h",
            "horizon_candles": horizon, "atr_multiplier": atr_multiplier, "source_rows": len(df), "feature_count": len(self.feature_names),
            "execution_filter": {"round_trip_cost": self.round_trip_cost, "min_edge": self.min_edge, "min_confidence": self.min_confidence},
            "splits": {"train": len(X_train), "validation": len(X_val), "test": len(X_test), "purge_gap_candles": horizon,
                       "test_start": str(X_test.index[0])},
            "prediction_metrics": {"return_mae": float(mean_absolute_error(y_test, predicted_returns)),
                                   "label_accuracy": float(accuracy_score(l_test, predicted_labels)),
                                   "label_balanced_accuracy": float(balanced_accuracy_score(l_test, predicted_labels)),
                                   "label_macro_f1": float(f1_score(l_test, predicted_labels, average="macro", zero_division=0))},
            "backtest": backtest,
        }
        self.is_trained = True
        return self.metrics

    def predict(self, df: pd.DataFrame) -> Tuple[int, float, Dict[str, float]]:
        features = feature_engineering.create_features(df).replace([np.inf, -np.inf], np.nan).fillna(0)
        X = features[self.feature_names].iloc[[-1]]
        expected_return, direction, confidence = self._signals(X)
        side = int(np.sign(expected_return[0]))
        active = side != 0 and side == int(direction[0]) and confidence[0] >= self.min_confidence and abs(expected_return[0]) >= self.round_trip_cost + self.min_edge
        signal = side if active else 0
        # Compatible avec l'API existante. Les probabilités de classe restent accessibles côté UI.
        probabilities = self.direction_model.predict_proba(X)[0]
        return signal, float(confidence[0] * 100), {"SELL": float(probabilities[0] * 100), "HOLD": float(probabilities[1] * 100), "BUY": float(probabilities[2] * 100)}

    def save(self) -> Path:
        if not self.is_trained:
            raise ValueError("Aucun modèle V2 à sauvegarder.")
        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"return_model": self.return_model, "direction_model": self.direction_model,
                   "confidence_calibrator": self.confidence_calibrator, "feature_names": self.feature_names,
                   "metrics": self.metrics, "horizon": self.horizon, "round_trip_cost": self.round_trip_cost,
                   "min_confidence": self.min_confidence, "min_edge": self.min_edge}
        temporary = self.artifact_path.with_suffix(".joblib.tmp")
        joblib.dump(payload, temporary)
        temporary.replace(self.artifact_path)
        self.manifest_path.write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.artifact_path

    def load(self) -> None:
        payload = joblib.load(self.artifact_path)
        self.return_model, self.direction_model = payload["return_model"], payload["direction_model"]
        self.confidence_calibrator, self.feature_names, self.metrics = payload["confidence_calibrator"], payload["feature_names"], payload["metrics"]
        self.horizon, self.round_trip_cost = payload["horizon"], payload["round_trip_cost"]
        self.min_confidence, self.min_edge, self.is_trained = payload["min_confidence"], payload["min_edge"], True


trading_model_v2 = TradingModelV2()
