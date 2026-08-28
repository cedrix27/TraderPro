"""Public Futures context collector, designed to accept additional providers later."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.models import MarketIntelligence
from app.services.binance_service import binance_service
from app.services.demo_trading_service import demo_trading_service


class MarketIntelligenceService:
    def initialize(self) -> None:
        with demo_trading_service._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS market_intelligence_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                funding_rate_pct REAL NOT NULL,
                open_interest REAL NOT NULL,
                day_change_pct REAL NOT NULL,
                volatility_pct REAL NOT NULL,
                context_score REAL NOT NULL,
                regime TEXT NOT NULL,
                bias TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS ix_intelligence_symbol_time ON market_intelligence_snapshots(symbol, created_at DESC)")

    async def get_context(self, symbol: str = "BTCUSDT") -> MarketIntelligence:
        symbol = symbol.upper()
        session = await binance_service._get_session()
        base_url = binance_service.FUTURES_DEMO_BASE_URL

        async def fetch(path: str) -> dict:
            async with session.get(f"{base_url}{path}", params={"symbol": symbol}) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    raise ValueError(payload.get("msg", "Donnée Futures indisponible."))
                return payload

        premium, open_interest, ticker = await asyncio.gather(
            fetch("/fapi/v1/premiumIndex"),
            fetch("/fapi/v1/openInterest"),
            fetch("/fapi/v1/ticker/24hr"),
        )
        price = float(premium["markPrice"])
        funding_rate_pct = float(premium.get("lastFundingRate", 0)) * 100
        oi = float(open_interest["openInterest"])
        day_change_pct = float(ticker.get("priceChangePercent", 0))
        low, high = float(ticker["lowPrice"]), float(ticker["highPrice"])
        volatility_pct = ((high - low) / price * 100) if price else 0.0

        with demo_trading_service._connect() as connection:
            previous = connection.execute("SELECT open_interest FROM market_intelligence_snapshots WHERE symbol = ? ORDER BY created_at DESC LIMIT 1", (symbol,)).fetchone()
        oi_change = ((oi - float(previous["open_interest"])) / float(previous["open_interest"]) * 100) if previous and previous["open_interest"] else None

        if volatility_pct >= 6:
            regime, bias = "high_volatility", "neutral"
        elif day_change_pct >= 1:
            regime, bias = "trend_up", "bullish"
        elif day_change_pct <= -1:
            regime, bias = "trend_down", "bearish"
        else:
            regime, bias = "range", "neutral"

        score = 50 + max(-15, min(15, day_change_pct * 3))
        if oi_change is not None:
            score += max(-8, min(8, oi_change * (1 if bias == "bullish" else -1)))
        if abs(funding_rate_pct) >= 0.03:
            score -= 8
        if regime == "high_volatility":
            score -= 15
        score = round(max(0, min(100, score)), 1)
        recommendation = (
            "Contexte favorable au suivi de tendance" if regime == "trend_up" and score >= 60 else
            "Contexte baissier : prudence sur les LONG" if regime == "trend_down" else
            "Volatilité élevée : privilégier l'attente" if regime == "high_volatility" else
            "Marché sans avantage directionnel clair"
        )
        result = MarketIntelligence(symbol=symbol, price=price, day_change_pct=round(day_change_pct, 2),
            funding_rate_pct=round(funding_rate_pct, 4), open_interest=oi,
            open_interest_change_pct=round(oi_change, 2) if oi_change is not None else None,
            volatility_pct=round(volatility_pct, 2), regime=regime, bias=bias, context_score=score,
            recommendation=recommendation, sources=["Binance USD-M Futures Demo"], timestamp=datetime.now(timezone.utc))
        with demo_trading_service._connect() as connection:
            connection.execute("""INSERT INTO market_intelligence_snapshots
                (symbol, price, funding_rate_pct, open_interest, day_change_pct, volatility_pct, context_score, regime, bias, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (result.symbol, result.price, result.funding_rate_pct,
                result.open_interest, result.day_change_pct, result.volatility_pct, result.context_score,
                result.regime, result.bias, result.timestamp.isoformat()))
        return result


market_intelligence_service = MarketIntelligenceService()
