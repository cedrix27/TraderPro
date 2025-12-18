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
    api_port: int = 8000

    # Binance API
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None

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
