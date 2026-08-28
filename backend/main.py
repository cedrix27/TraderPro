"""
TraderPro API - Point d'entrée principal

Lancer l'application:
    uvicorn main:app --reload --host 0.0.0.0 --port 8002

Documentation API:
    http://localhost:8002/docs (Swagger UI)
    http://localhost:8002/redoc (ReDoc)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os

from app.core.config import settings
from app.api import router
from app.services.binance_service import binance_service
from app.services.demo_trading_service import demo_trading_service
from app.services.autonomous_trading_service import autonomous_trading_service
from app.services.learning_service import learning_service
from app.services.market_intelligence_service import market_intelligence_service
from app.ml.model import trading_model
from app.ml.model_v2 import trading_model_v2
from app.ml.ttm_prediction_service import ttm_prediction_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application

    Startup:
    - Charger le modèle ML s'il existe

    Shutdown:
    - Fermer les connexions
    """
    # Startup
    print("🚀 Démarrage de TraderPro API...")
    demo_trading_service.initialize()
    print("✅ Journal de trading démo initialisé")
    autonomous_trading_service.initialize()
    print("✅ Journal d'expériences autonomes initialisé")
    learning_service.initialize()
    print("✅ Registre champion/challenger initialisé")
    market_intelligence_service.initialize()
    print("✅ Journal Intelligence Marché initialisé")

    # Essayer de charger un modèle existant
    if trading_model.artifact_path.exists():
        try:
            trading_model.load()
            print("✅ Modèle ML chargé")
        except Exception as e:
            print(f"⚠️ Impossible de charger le modèle: {e}")
    else:
        print("ℹ️ Aucun modèle ML trouvé. Utilisez POST /api/model/train pour en créer un.")

    if trading_model_v2.artifact_path.exists():
        try:
            trading_model_v2.load()
            print("✅ Rapport modèle V2 chargé (non activé pour le trading)")
        except Exception as e:
            print(f"⚠️ Impossible de charger le modèle V2: {e}")

    # Charger le modèle TTM s'il existe
    ttm_status = ttm_prediction_service.get_status()
    if ttm_status['model_exists']:
        try:
            success = ttm_prediction_service.load_model()
            if success:
                print("✅ Modèle TTM chargé")
            else:
                print("⚠️ Impossible de charger le modèle TTM")
        except Exception as e:
            print(f"⚠️ Erreur chargement TTM: {e}")
    else:
        print("ℹ️ Modèle TTM non trouvé. Utilisez colab_ttm_finetuning.ipynb pour l'entraîner.")

    async def autonomous_loop() -> None:
        while True:
            try:
                result = await autonomous_trading_service.run_once()
                autonomous_trading_service.sync_experiences()
                if result["status"] not in {"disabled", "skipped"}:
                    print(f"🤖 Cycle autonome : {result['status']} ({result.get('action', 'HOLD')})")
            except Exception as exc:
                print(f"⚠️ Cycle autonome en erreur [{type(exc).__name__}] : {exc!r}")
            await asyncio.sleep(max(60, settings.autonomous_scheduler_seconds))

    autonomous_task = asyncio.create_task(autonomous_loop())
    try:
        yield
    finally:
        autonomous_task.cancel()
        try:
            await autonomous_task
        except asyncio.CancelledError:
            pass

        # Shutdown
        print("👋 Arrêt de TraderPro API...")
        await binance_service.close()


# Créer l'application FastAPI
app = FastAPI(
    title="TraderPro API",
    description="""
## 🤖 Assistant IA de Trading Bitcoin

TraderPro est une plateforme d'analyse et de trading Bitcoin assistée par Intelligence Artificielle.

### Fonctionnalités

* 📊 **Données de marché** - Prix en temps réel et données historiques via Binance
* 📈 **Analyse technique** - RSI, MACD, Bollinger Bands, Support/Résistance
* 🎯 **Signaux de trading** - BUY/SELL/HOLD avec niveaux entry/SL/TP
* 🤖 **Prédictions ML** - Modèle XGBoost entraîné sur les données historiques
* 💬 **Assistant IA** - Chat interactif pour poser vos questions

### Utilisation

1. **Obtenir une analyse**: `GET /api/analysis`
2. **Signal rapide**: `GET /api/analysis/signal`
3. **Prédiction ML**: `GET /api/predict` (après avoir entraîné le modèle)
4. **Chat**: `POST /api/chat` avec votre question

### Avertissement

⚠️ Le trading comporte des risques. Les analyses et signaux fournis sont à titre informatif uniquement.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Must be False when using "*" for origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Inclure les routes
app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "name": "TraderPro API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
