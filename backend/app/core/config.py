"""
Configuration de l'application TraderPro
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuration globale de l'application"""

    # Application
    app_name: str = "TraderPro API"
    app_version: str = "1.0.0"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8002

    # Binance API
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None
    # Dedicated credentials created on Binance USD-M Futures Testnet.
    binance_futures_testnet_api_key: Optional[str] = None
    binance_futures_testnet_api_secret: Optional[str] = None
    futures_leverage: int = 1

    # Autonomous Testnet trader. Disabled unless explicitly enabled in backend/.env.
    autonomous_trading_enabled: bool = False
    autonomous_symbol: str = "BTCUSDT"
    autonomous_trade_amount_usdt: float = 60.0
    autonomous_max_daily_loss_usdt: float = 20.0
    autonomous_max_trades_per_day: int = 4
    autonomous_min_confidence: float = 55.0
    autonomous_scheduler_seconds: int = 300

    # Trading Configuration
    default_symbol: str = "BTCUSDT"
    default_timeframe: str = "1h"

    # ML Model
    model_path: str = "models/trading_model.joblib"

    # Database
    database_url: str = "sqlite:///./data/traderpro.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        protected_namespaces = ()


# Instance globale des settings
settings = Settings()
