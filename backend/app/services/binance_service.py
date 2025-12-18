"""
Service pour interagir avec l'API Binance
Récupère les données de marché en temps réel et historiques
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
from app.core.config import settings
from app.core.models import OHLCV, MarketData


class BinanceService:
    """
    Service pour récupérer les données de Binance

    Utilise l'API publique de Binance (pas besoin de clé API pour les données publiques)
    Documentation: https://binance-docs.github.io/apidocs/spot/en/
    """

    BASE_URL = "https://api.binance.com/api/v3"

    # Mapping des timeframes Binance
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1D": "1d",
        "1w": "1w",
        "1W": "1w",
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtenir ou créer une session HTTP"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Fermer la session HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(self, endpoint: str, params: dict = None) -> Any:
        """Faire une requête à l'API Binance"""
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    raise Exception(f"Binance API Error: {response.status} - {error_msg}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network Error: {str(e)}")

    async def get_current_price(self, symbol: str = "BTCUSDT") -> MarketData:
        """
        Récupérer le prix actuel et les stats 24h

        Args:
            symbol: Paire de trading (ex: BTCUSDT)

        Returns:
            MarketData avec prix et variations
        """
        data = await self._request("ticker/24hr", {"symbol": symbol})

        return MarketData(
            symbol=symbol,
            price=float(data["lastPrice"]),
            change_24h=float(data["priceChange"]),
            change_percent_24h=float(data["priceChangePercent"]),
            high_24h=float(data["highPrice"]),
            low_24h=float(data["lowPrice"]),
            volume_24h=float(data["quoteVolume"]),
            timestamp=datetime.now()
        )

    async def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[OHLCV]:
        """
        Récupérer les données OHLCV (bougies)

        Args:
            symbol: Paire de trading
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Nombre de bougies (max 1000)
            start_time: Timestamp de début (ms)
            end_time: Timestamp de fin (ms)

        Returns:
            Liste de OHLCV
        """
        params = {
            "symbol": symbol,
            "interval": self.TIMEFRAME_MAP.get(interval, interval),
            "limit": min(limit, 1000)
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        data = await self._request("klines", params)

        klines = []
        for k in data:
            klines.append(OHLCV(
                timestamp=k[0],  # Open time
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5])
            ))

        return klines

    async def get_historical_data(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Récupérer les données historiques sous forme de DataFrame

        Args:
            symbol: Paire de trading
            interval: Timeframe
            days: Nombre de jours d'historique

        Returns:
            DataFrame avec colonnes: timestamp, open, high, low, close, volume
        """
        # Calculer le timestamp de début
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        all_klines = []
        current_start = start_time

        # Binance limite à 1000 bougies par requête, on boucle si nécessaire
        while current_start < end_time:
            klines = await self.get_klines(
                symbol=symbol,
                interval=interval,
                limit=1000,
                start_time=current_start,
                end_time=end_time
            )

            if not klines:
                break

            all_klines.extend(klines)

            # Avancer au prochain batch
            current_start = klines[-1].timestamp + 1

            # Petit délai pour éviter le rate limiting
            await asyncio.sleep(0.1)

        # Convertir en DataFrame
        df = pd.DataFrame([k.model_dump() for k in all_klines])

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[~df.index.duplicated(keep='last')]
            df.sort_index(inplace=True)

        return df

    async def get_orderbook(self, symbol: str = "BTCUSDT", limit: int = 100) -> Dict:
        """
        Récupérer le carnet d'ordres

        Args:
            symbol: Paire de trading
            limit: Profondeur du carnet (5, 10, 20, 50, 100, 500, 1000)

        Returns:
            Dict avec bids et asks
        """
        data = await self._request("depth", {"symbol": symbol, "limit": limit})
        return {
            "bids": [(float(price), float(qty)) for price, qty in data["bids"]],
            "asks": [(float(price), float(qty)) for price, qty in data["asks"]],
            "timestamp": datetime.now()
        }

    async def get_recent_trades(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Dict]:
        """
        Récupérer les trades récents

        Args:
            symbol: Paire de trading
            limit: Nombre de trades

        Returns:
            Liste des trades récents
        """
        data = await self._request("trades", {"symbol": symbol, "limit": limit})
        return [
            {
                "price": float(t["price"]),
                "quantity": float(t["qty"]),
                "time": datetime.fromtimestamp(t["time"] / 1000),
                "is_buyer_maker": t["isBuyerMaker"]
            }
            for t in data
        ]


# Instance singleton
binance_service = BinanceService()
