"""
Script d'entraînement du modèle ML

Usage:
    python scripts/train_model.py

Ce script:
1. Télécharge les données historiques de Binance
2. Crée les features
3. Entraîne le modèle XGBoost
4. Sauvegarde le modèle

============ GUIDE D'ENTRAÎNEMENT ============

Pour un bon modèle de trading:

1. DONNÉES
   - Minimum 90 jours de données
   - Timeframe: 1h ou 4h recommandé
   - Plus de données = meilleure généralisation

2. LABELLING
   - Threshold: 2% par défaut
   - Horizon: 4 périodes (4h avec timeframe 1h)
   - Ajustez selon votre stratégie

3. ÉVALUATION
   - Accuracy > 55% est bon pour le trading
   - Vérifiez le backtesting avant d'utiliser en réel
   - Attention à l'overfitting!

4. MISE À JOUR
   - Réentraînez régulièrement (hebdomadaire)
   - Les conditions de marché changent
"""
import asyncio
import sys
import os

# Ajouter le path parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.binance_service import BinanceService
from app.ml.model import TradingModel


async def main():
    print("=" * 60)
    print("TraderPro - Entraînement du Modèle ML")
    print("=" * 60)

    # Configuration
    symbol = "BTCUSDT"
    timeframe = "1h"
    days = 90
    horizon = 4
    threshold = 0.02

    print(f"""
Configuration:
- Symbol: {symbol}
- Timeframe: {timeframe}
- Données: {days} jours
- Horizon: {horizon} périodes
- Threshold: {threshold * 100}%
""")

    # Initialiser les services
    binance = BinanceService()
    model = TradingModel()

    try:
        # 1. Télécharger les données
        print("📥 Téléchargement des données depuis Binance...")
        df = await binance.get_historical_data(
            symbol=symbol,
            interval=timeframe,
            days=days
        )

        if df.empty:
            print("❌ Erreur: Pas de données récupérées")
            return

        print(f"   ✓ {len(df)} bougies récupérées")
        print(f"   ✓ Période: {df.index[0]} à {df.index[-1]}")

        # 2. Entraîner le modèle
        print("\n🤖 Entraînement du modèle...")
        metrics = model.train(
            df,
            horizon=horizon,
            threshold=threshold
        )

        # 3. Afficher les résultats
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DE L'ENTRAÎNEMENT")
        print("=" * 60)
        print(f"""
Accuracy: {metrics['accuracy']:.2%}

Classification Report:
- BUY:  Precision={metrics['classification_report']['BUY']['precision']:.2f}, Recall={metrics['classification_report']['BUY']['recall']:.2f}
- HOLD: Precision={metrics['classification_report']['HOLD']['precision']:.2f}, Recall={metrics['classification_report']['HOLD']['recall']:.2f}
- SELL: Precision={metrics['classification_report']['SELL']['precision']:.2f}, Recall={metrics['classification_report']['SELL']['recall']:.2f}

Top Features:
""")
        for i, feat in enumerate(metrics['top_features'][:5], 1):
            print(f"  {i}. {feat['feature']}: {feat['importance']:.4f}")

        # 4. Sauvegarder
        print("\n💾 Sauvegarde du modèle...")
        model.save()

        # 5. Test de prédiction
        print("\n🔮 Test de prédiction...")
        signal, confidence, probabilities = model.predict(df)

        signal_map = {1: "BUY", 0: "HOLD", -1: "SELL"}
        print(f"""
Prédiction actuelle:
- Signal: {signal_map[signal]}
- Confiance: {confidence:.1f}%
- Probabilités: BUY={probabilities['BUY']:.1f}%, HOLD={probabilities['HOLD']:.1f}%, SELL={probabilities['SELL']:.1f}%
""")

        print("✅ Entraînement terminé avec succès!")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise
    finally:
        await binance.close()


if __name__ == "__main__":
    asyncio.run(main())
