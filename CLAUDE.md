# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TraderPro is an AI-powered Bitcoin trading assistant combining technical analysis, XGBoost classification, LSTM deep learning, TTM (Tiny Time Mixer) transformers, and Reinforcement Learning (PPO). Full-stack app: FastAPI backend + Next.js frontend.

## Development Commands

### Backend (Python 3.13 / FastAPI)
```bash
cd backend
python -m venv venv                   # First-time setup
source venv/bin/activate              # Activate virtualenv
pip install -r requirements.txt       # Install dependencies
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8002  # Run server

# Training
python scripts/train_model.py         # Train XGBoost model

# Testing
pytest                                 # Run all tests
pytest tests/test_specific.py         # Run single test file
pytest -k "test_name"                  # Run tests matching pattern
```

Note: No `backend/tests/` directory exists yet. Tests need to be created.

### Frontend (Next.js 16 / React 19 / TailwindCSS 4)
```bash
cd frontend
npm install                           # Install dependencies
npm run dev                           # Development server (port 3000)
npm run build                         # Production build
npm run lint                          # ESLint
```

### API Documentation
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Architecture

### Backend (`backend/`)
- **main.py**: FastAPI app with lifespan handler that loads ML models (XGBoost, TTM) on startup and closes Binance connection on shutdown
- **app/api/routes.py**: Single file containing all REST endpoints (~30 routes). All route groups: market data, analysis, ML predictions, LSTM predictions, TTM predictions, trading plans, chat assistant
- **app/core/config.py**: Pydantic `Settings` class reading from `.env`. Global singleton: `settings`
- **app/core/models.py**: All Pydantic request/response models and enums (`SignalType`, `TrendType`, `RiskLevel`, etc.)
- **app/services/**: Business logic singletons — `binance_service` (Binance API), `analysis_service` (signal generation), `indicators_service` (RSI, MACD, Bollinger Bands, etc.)
- **app/ml/**: ML model implementations — each exposes a singleton instance (`trading_model`, `prediction_service`, `ttm_prediction_service`)

### Frontend (`frontend/src/`)
- **lib/api/client.ts**: Typed API client wrapping all backend endpoints with `fetchApi<T>()` generic
- **hooks/**: Data-fetching hooks (`useMarketData`, `useAnalysis`, `usePrediction`, `useChat`, `useTradingPlans`, `useApiHealth`) — these are the primary interface between components and the API
- **components/**: Organized by feature (dashboard, analysis, plans, ai-assistant, charts, layout). UI primitives use Radix UI + shadcn/ui pattern
- **app/**: Next.js App Router pages (dashboard, analysis, prediction, plans, assistant)

### Data Flow
```
Frontend Hooks → API Client → FastAPI Routes → Services → Binance/ML → Response
```

## Key Patterns

- **Singletons everywhere**: Services (`binance_service`, `analysis_service`) and ML models (`trading_model`, `prediction_service`, `ttm_prediction_service`) are instantiated at module level and imported directly
- **All backend I/O is async**: Routes and service methods use async/await
- **Pydantic for everything**: Request validation, response serialization, and app configuration all use Pydantic models
- **Feature engineering pipeline**: Raw OHLCV data → 50+ derived features (in `ml/features.py`) → ML model input

## ML Models

| Model | Input | Output | File |
|-------|-------|--------|------|
| XGBoost | 50+ engineered features | BUY/HOLD/SELL | `ml/model.py` |
| LSTM | 14-day price history | UP/DOWN | `ml/prediction_service.py` |
| TTM (Transformer) | 64-day price history | UP/DOWN | `ml/ttm_prediction_service.py` |
| PPO (planned) | State + position | Trading strategy | `colab_rl_training.ipynb` |

TTM model files: `backend/app/ml/models/ttm/` (`config.json`, `model.safetensors`, `preprocessor.pkl`, `ttm_config.json`). Fine-tuning notebook: `colab_ttm_finetuning.ipynb`.

## Important Defaults

- Default trading pair: `BTCUSDT`, default timeframe: `1h` (configured in `app/core/config.py`)
- XGBoost model path: `backend/models/trading_model.joblib`
- All ML file paths in the table above are relative to `backend/app/`

## Environment Variables

Backend `.env` (in `backend/`):
```
BINANCE_API_KEY=          # Optional (public data only)
BINANCE_API_SECRET=       # Optional
BINANCE_TESTNET=true
API_HOST=0.0.0.0
API_PORT=8002
```

Frontend `.env.local` (in `frontend/`):
```
NEXT_PUBLIC_API_URL=http://localhost:8002/api
```

## Documentation

- Comprehensive backend guide: `backend/GUIDE_BACKEND.md` (includes ML/RL theory explanations)
