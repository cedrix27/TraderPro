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
import hashlib
import hmac
from decimal import Decimal, ROUND_DOWN
from urllib.parse import urlencode
from app.core.config import settings
from app.core.models import OHLCV, MarketData


class BinanceService:
    """
    Service pour récupérer les données de Binance

    Utilise l'API publique de Binance (pas besoin de clé API pour les données publiques)
    Documentation: https://binance-docs.github.io/apidocs/spot/en/
    """

    BASE_URL = "https://api.binance.com/api/v3"
    PUBLIC_DATA_BASE_URL = "https://data-api.binance.vision/api/v3"
    US_PUBLIC_BASE_URL = "https://api.binance.us/api/v3"
    TESTNET_BASE_URL = "https://testnet.binance.vision/api/v3"
    FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
    FUTURES_DEMO_BASE_URL = "https://demo-fapi.binance.com"

    # Equivalent USD-M Futures public endpoints. This fallback keeps market
    # analysis available when the Spot API domains are unavailable locally.
    FUTURES_PUBLIC_ENDPOINTS = {
        "ticker/24hr": "/fapi/v1/ticker/24hr",
        "klines": "/fapi/v1/klines",
        "depth": "/fapi/v1/depth",
        "trades": "/fapi/v1/trades",
    }


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
        """Faire une requête publique avec repli Spot puis Futures Demo."""
        session = await self._get_session()
        errors = []
        for base_url in (self.BASE_URL, self.PUBLIC_DATA_BASE_URL, self.US_PUBLIC_BASE_URL):
            try:
                async with session.get(f"{base_url}/{endpoint}", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    errors.append(f"{base_url}: HTTP {response.status} - {await response.text()}")
            except aiohttp.ClientError as exc:
                errors.append(f"{base_url}: {exc}")

        futures_endpoint = self.FUTURES_PUBLIC_ENDPOINTS.get(endpoint)
        if futures_endpoint:
            try:
                async with session.get(f"{self.FUTURES_DEMO_BASE_URL}{futures_endpoint}", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    errors.append(f"{self.FUTURES_DEMO_BASE_URL}: HTTP {response.status} - {await response.text()}")
            except aiohttp.ClientError as exc:
                errors.append(f"{self.FUTURES_DEMO_BASE_URL}: {exc}")
        raise Exception("Binance API indisponible : " + " | ".join(errors))

    async def _testnet_signed_request(self, method: str, endpoint: str, params: dict) -> Any:
        """Call Binance Spot Testnet only. Production endpoints are never used here."""
        if not settings.binance_testnet:
            raise ValueError("Le trading démo exige BINANCE_TESTNET=true.")
        if not settings.binance_testnet_api_key or not settings.binance_testnet_api_secret:
            raise ValueError("Configurez BINANCE_TESTNET_API_KEY et BINANCE_TESTNET_API_SECRET côté backend.")

        signed_params = {**params, "timestamp": int(datetime.now().timestamp() * 1000), "recvWindow": 5000}
        query = urlencode(signed_params)
        signature = hmac.new(
            settings.binance_testnet_api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        url = f"{self.TESTNET_BASE_URL}/{endpoint}?{query}&signature={signature}"
        session = await self._get_session()
        headers = {"X-MBX-APIKEY": settings.binance_testnet_api_key}
        try:
            async with session.request(method, url, headers=headers) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    raise ValueError(payload.get("msg", f"Binance Testnet HTTP {response.status}"))
                return payload
        except aiohttp.ClientError as exc:
            raise ValueError(f"Erreur réseau Binance Testnet: {exc}") from exc

    async def _testnet_quantity(self, symbol: str, quantity: float) -> str:
        """Round a sell quantity down to the symbol's Binance LOT_SIZE step."""
        session = await self._get_session()
        url = f"{self.TESTNET_BASE_URL}/exchangeInfo"
        async with session.get(url, params={"symbol": symbol}) as response:
            data = await response.json(content_type=None)
            if response.status >= 400 or not data.get("symbols"):
                raise ValueError(data.get("msg", "Paire indisponible sur Binance Testnet."))
        filters = data["symbols"][0].get("filters", [])
        lot_size = next((item for item in filters if item.get("filterType") == "LOT_SIZE"), None)
        if lot_size is None:
            raise ValueError("Filtre LOT_SIZE Binance introuvable.")
        step = Decimal(lot_size["stepSize"])
        rounded = (Decimal(str(quantity)) / step).to_integral_value(rounding=ROUND_DOWN) * step
        if rounded < Decimal(lot_size["minQty"]):
            raise ValueError("Quantité insuffisante pour un ordre Binance Testnet.")
        return format(rounded, "f")

    async def create_testnet_market_buy(self, symbol: str, amount_usdt: float) -> Dict[str, Any]:
        return await self._testnet_signed_request(
            "POST", "order", {"symbol": symbol.upper(), "side": "BUY", "type": "MARKET", "quoteOrderQty": str(amount_usdt)}
        )

    async def create_testnet_market_sell(self, symbol: str, quantity: float) -> Dict[str, Any]:
        rounded_quantity = await self._testnet_quantity(symbol.upper(), quantity)
        return await self._testnet_signed_request(
            "POST", "order", {"symbol": symbol.upper(), "side": "SELL", "type": "MARKET", "quantity": rounded_quantity}
        )

    async def _futures_signed_request(self, method: str, endpoint: str, params: dict) -> Any:
        """USD-M Futures Testnet only; no production URL is present in this method."""
        key, secret = settings.binance_futures_testnet_api_key, settings.binance_futures_testnet_api_secret
        if not settings.binance_testnet or not key or not secret:
            raise ValueError("Configurez BINANCE_FUTURES_TESTNET_API_KEY et BINANCE_FUTURES_TESTNET_API_SECRET.")
        signed = {**params, "timestamp": int(datetime.now().timestamp() * 1000), "recvWindow": 5000}
        query = urlencode(signed)
        signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        session = await self._get_session()
        try:
            async with session.request(method, f"{self.FUTURES_TESTNET_BASE_URL}{endpoint}?{query}&signature={signature}", headers={"X-MBX-APIKEY": key}) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    raise ValueError(payload.get("msg", f"Futures Testnet HTTP {response.status}"))
                return payload
        except aiohttp.ClientError as exc:
            raise ValueError(f"Erreur réseau Binance Futures Testnet: {exc}") from exc

    async def _futures_quantity(self, symbol: str, quantity: float) -> str:
        session = await self._get_session()
        async with session.get(f"{self.FUTURES_TESTNET_BASE_URL}/fapi/v1/exchangeInfo") as response:
            data = await response.json(content_type=None)
        item = next((entry for entry in data.get("symbols", []) if entry.get("symbol") == symbol.upper()), None)
        if item is None:
            raise ValueError("Paire indisponible sur Binance Futures Testnet.")
        lot = next((entry for entry in item.get("filters", []) if entry.get("filterType") == "LOT_SIZE"), None)
        if lot is None:
            raise ValueError("Filtre LOT_SIZE Futures introuvable.")
        step = Decimal(lot["stepSize"])
        rounded = (Decimal(str(quantity)) / step).to_integral_value(rounding=ROUND_DOWN) * step
        if rounded < Decimal(lot["minQty"]):
            raise ValueError("Montant inférieur à la taille minimale Futures.")
        return format(rounded, "f")

    async def configure_futures_isolated_1x(self, symbol: str) -> None:
        try:
            await self._futures_signed_request("POST", "/fapi/v1/marginType", {"symbol": symbol.upper(), "marginType": "ISOLATED"})
        except ValueError as exc:
            if "No need to change margin type" not in str(exc):
                raise
        await self._futures_signed_request("POST", "/fapi/v1/leverage", {"symbol": symbol.upper(), "leverage": settings.futures_leverage})

    async def get_futures_mark_price(self, symbol: str) -> float:
        session = await self._get_session()
        async with session.get(f"{self.FUTURES_TESTNET_BASE_URL}/fapi/v1/premiumIndex", params={"symbol": symbol.upper()}) as response:
            payload = await response.json(content_type=None)
            if response.status >= 400:
                raise ValueError(payload.get("msg", "Mark price Futures indisponible."))
        return float(payload["markPrice"])

    async def create_futures_market_order(self, symbol: str, side: str, quantity: float, *, reduce_only: bool = False) -> Dict[str, Any]:
        rounded = await self._futures_quantity(symbol, quantity)
        params = {"symbol": symbol.upper(), "side": side, "type": "MARKET", "quantity": rounded, "newOrderRespType": "RESULT"}
        if reduce_only:
            params["reduceOnly"] = "true"
        return await self._futures_signed_request("POST", "/fapi/v1/order", params)

    async def create_futures_protective_orders(self, symbol: str, entry_side: str, stop_loss: float, take_profit: float) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Place stop-loss and take-profit orders that close the whole Testnet position."""
        close_side = "SELL" if entry_side == "BUY" else "BUY"
        common = {"algoType": "CONDITIONAL", "symbol": symbol.upper(), "side": close_side, "closePosition": "true", "workingType": "MARK_PRICE"}
        stop = await self._futures_signed_request("POST", "/fapi/v1/algoOrder", {
            **common, "type": "STOP_MARKET", "triggerPrice": f"{stop_loss:.2f}",
        })
        try:
            take_profit_order = await self._futures_signed_request("POST", "/fapi/v1/algoOrder", {
                **common, "type": "TAKE_PROFIT_MARKET", "triggerPrice": f"{take_profit:.2f}",
            })
        except ValueError:
            await self.cancel_futures_order(symbol, str(stop.get("orderId", "")))
            raise
        return stop, take_profit_order

    async def cancel_futures_order(self, symbol: str, order_id: str) -> None:
        if order_id:
            await self._futures_signed_request("DELETE", "/fapi/v1/algoOrder", {"symbol": symbol.upper(), "algoId": order_id})

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
