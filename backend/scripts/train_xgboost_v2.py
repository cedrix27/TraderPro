"""Entraînement long V2 : cinq ans BTC 1h, walk-forward et artefact de production Testnet."""
import asyncio
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.model_v2 import TradingModelV2
from app.services.binance_service import BinanceService


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-fold", type=int, default=0)
    parser.add_argument("--fold-count", type=int, default=3)
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    service = BinanceService()
    try:
        cache = Path("data/BTCUSDT_1h_5y.csv")
        if cache.exists():
            candles = pd.read_csv(cache, index_col="timestamp", parse_dates=True)
            print(f"Cache local chargé : {cache}", flush=True)
        else:
            candles = await service.get_historical_data("BTCUSDT", "1h", days=5 * 365)
            cache.parent.mkdir(parents=True, exist_ok=True)
            candles.to_csv(cache)
        if len(candles) < 40_000:
            raise RuntimeError(f"Historique insuffisant : {len(candles)} bougies (40 000 requis).")
        print(f"Données prêtes : {len(candles)} bougies, cache {cache}", flush=True)

        checkpoint = Path("data/xgboost_v2_walk_forward.json")
        model = TradingModelV2()
        walk_forward = model.walk_forward_backtest(candles, start_fold=args.start_fold, max_folds=args.fold_count)
        prior = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"folds": []}
        merged = {item["test_start"]: item for item in prior["folds"]}
        merged.update({item["test_start"]: item for item in walk_forward["folds"]})
        prior["folds"] = [merged[key] for key in sorted(merged)]
        checkpoint.write_text(json.dumps(prior, indent=2), encoding="utf-8")
        print(f"Checkpoint walk-forward : {len(prior['folds'])} fenêtres sauvegardées", flush=True)
        if not args.finalize:
            return

        # L'artefact final est entraîné sur tout l'historique disponible ; le checkpoint reste
        # le rapport indépendant, construit uniquement par fenêtres walk-forward.
        metrics = model.train(candles)
        fold_returns = [item["net_return"] for item in prior["folds"]]
        aggregate_curve = np.cumprod([1.0] + [1.0 + value for value in fold_returns])
        aggregate_drawdown = 1 - aggregate_curve / np.maximum.accumulate(aggregate_curve)
        metrics["walk_forward"] = {
            "method": walk_forward["method"], "folds": prior["folds"],
            "aggregate": {"fold_count": len(prior["folds"]), "trades": sum(item["trades"] for item in prior["folds"]),
                          "net_return": float(aggregate_curve[-1] - 1), "max_drawdown": float(aggregate_drawdown.max())},
        }
        model.metrics = metrics
        artifact = model.save()
        print(f"Artefact V2 sauvegardé : {artifact}", flush=True)
        print(f"Holdout final : {metrics['backtest']}", flush=True)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
