"""Entraîne et sauvegarde le modèle XGBoost sélectionné par grille temporelle."""
import asyncio
from pathlib import Path

from app.ml.model import TradingModel
from app.services.binance_service import BinanceService


async def main() -> None:
    service = BinanceService()
    try:
        candles = await service.get_historical_data("BTCUSDT", "1h", days=365)
        if len(candles) < 5_000:
            raise RuntimeError(f"Historique insuffisant : {len(candles)} bougies.")

        cache_path = Path("data/xgboost_BTCUSDT_1h_365d.csv")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        candles.to_csv(cache_path)
        print(f"Données : {len(candles)} bougies, cache : {cache_path}", flush=True)

        model = TradingModel()
        metrics = model.train(candles, horizon=4, threshold=0.004, grid_search=True)
        artifact = model.save()
        tuning, test = metrics["hyperparameter_search"], metrics["test_metrics"]
        print(f"Artefact : {artifact}", flush=True)
        print(f"Grille : {tuning['candidates']} candidats, CV macro-F1={tuning['best_cv_macro_f1']:.4f}", flush=True)
        print(f"Paramètres : {tuning['best_params']}", flush=True)
        print(f"Test : accuracy={test['accuracy']:.4f}, macro_f1={test['macro_f1']:.4f}, balanced_accuracy={test['balanced_accuracy']:.4f}", flush=True)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
