"""
TraderPro API - Point d'entrée principal

Lancer l'application:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Documentation API:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api import router
from app.services.binance_service import binance_service
from app.ml.model import trading_model


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

    # Essayer de charger un modèle existant
    if os.path.exists(settings.model_path):
        try:
            trading_model.load()
            print("✅ Modèle ML chargé")
        except Exception as e:
            print(f"⚠️ Impossible de charger le modèle: {e}")
    else:
        print("ℹ️ Aucun modèle ML trouvé. Utilisez POST /api/model/train pour en créer un.")

    yield

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
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:8005",      # API docs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
