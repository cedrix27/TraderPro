"""Autonomous, guarded Futures Testnet decision loop.

The strategy is deliberately deterministic today. The stored experiences are the dataset
for future champion/challenger retraining; they do not mutate a model after one trade.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.core.config import settings
from app.core.models import SignalType, TradingSignal, TrendType
from app.services.analysis_service import analysis_service
from app.services.demo_trading_service import demo_trading_service
from app.services.market_intelligence_service import market_intelligence_service


class AutonomousTradingService:
    def initialize(self) -> None:
        with demo_trading_service._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS autonomous_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candle_key TEXT NOT NULL UNIQUE,
                    regime TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS autonomous_experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    features_json TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    decision_id INTEGER,
                    trade_id INTEGER,
                    pnl_usdt REAL,
                    outcome TEXT NOT NULL DEFAULT 'pending',
                    resolved_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES autonomous_runs(id)
                );
            """)
            existing = {row[1] for row in connection.execute("PRAGMA table_info(autonomous_experiences)")}
            for name, definition in {
                "trade_id": "INTEGER", "pnl_usdt": "REAL", "outcome": "TEXT NOT NULL DEFAULT 'pending'", "resolved_at": "TEXT",
            }.items():
                if name not in existing:
                    connection.execute(f"ALTER TABLE autonomous_experiences ADD COLUMN {name} {definition}")

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _already_processed(self, candle_key: str) -> bool:
        with demo_trading_service._connect() as connection:
            return connection.execute("SELECT 1 FROM autonomous_runs WHERE candle_key = ?", (candle_key,)).fetchone() is not None

    def _daily_limits(self) -> tuple[bool, str | None]:
        today = self._now().date().isoformat()
        with demo_trading_service._connect() as connection:
            row = connection.execute("""SELECT COUNT(*) AS trades, COALESCE(SUM(pnl_usdt), 0) AS pnl
                FROM demo_trades WHERE date(opened_at) = ?""", (today,)).fetchone()
        if int(row["trades"]) >= settings.autonomous_max_trades_per_day:
            return False, "limite quotidienne de trades atteinte"
        if float(row["pnl"]) <= -settings.autonomous_max_daily_loss_usdt:
            return False, "perte quotidienne maximale atteinte"
        return True, None

    @staticmethod
    def _regime(analysis) -> str:
        atr = next((item.value for item in analysis.indicators if item.name == "ATR"), 0.0)
        if analysis.signal.entry and atr / analysis.signal.entry > 0.025:
            return "high_volatility"
        if analysis.trend_strength >= 60 and analysis.trend != TrendType.NEUTRAL:
            return "trend"
        return "range"

    def _adaptive_signal(self, analysis, regime: str) -> TradingSignal:
        indicators = {item.name: item.value for item in analysis.indicators}
        base = analysis.signal
        action, confidence, reason = SignalType.HOLD, base.confidence, "Aucun setup suffisamment robuste"
        if regime == "trend" and base.action != SignalType.HOLD and base.confidence >= settings.autonomous_min_confidence:
            action, reason = base.action, "Suivi de tendance : signal technique aligné"
        elif regime == "range":
            rsi = indicators.get("RSI", 50.0)
            if rsi <= 35:
                action, confidence, reason = SignalType.BUY, max(55.0, 70.0 - rsi / 2), "Range : RSI survendu, retour à la moyenne"
            elif rsi >= 65:
                action, confidence, reason = SignalType.SELL, max(55.0, 35.0 + rsi / 2), "Range : RSI suracheté, retour à la moyenne"
        elif regime == "high_volatility":
            reason = "Volatilité excessive : aucune nouvelle position"
        return TradingSignal(action=action, confidence=round(confidence, 1), entry=base.entry,
                             stop_loss=base.stop_loss, take_profit=base.take_profit,
                             risk_reward=base.risk_reward, reasoning=[f"Régime: {regime}", reason, *base.reasoning[:2]])

    async def run_once(self, *, force: bool = False) -> dict:
        now = self._now()
        candle_key = f"{settings.autonomous_symbol}:{now.strftime('%Y-%m-%dT%H')}"
        if not force and self._already_processed(candle_key):
            return {"status": "skipped", "reason": "bougie déjà traitée", "candle_key": candle_key}
        if not settings.autonomous_trading_enabled and not force:
            return {"status": "disabled", "reason": "AUTONOMOUS_TRADING_ENABLED=false", "candle_key": candle_key}

        analysis = await analysis_service.get_full_analysis(settings.autonomous_symbol, "1h")
        intelligence = await market_intelligence_service.get_context(settings.autonomous_symbol)
        regime, signal = self._regime(analysis), self._adaptive_signal(analysis, self._regime(analysis))
        permitted, rejection = self._daily_limits()
        open_trade = demo_trading_service._get_open_trade(settings.autonomous_symbol)
        if open_trade and signal.action.value == open_trade["side"].replace("LONG", "BUY").replace("SHORT", "SELL"):
            signal.action = SignalType.HOLD
            signal.reasoning.append("Position déjà ouverte dans le même sens")
        status, decision_id = "recorded", None
        if signal.action != SignalType.HOLD and permitted:
            decision = await demo_trading_service.execute_signal(signal, settings.autonomous_symbol, settings.autonomous_trade_amount_usdt)
            status, decision_id = decision.status, decision.id
        elif not permitted:
            status = "risk_rejected"
            signal.reasoning.append(rejection or "limite de risque")

        with demo_trading_service._connect() as connection:
            cursor = connection.execute("""INSERT INTO autonomous_runs (candle_key, regime, action, confidence, status, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (candle_key, regime, signal.action.value, signal.confidence, status, " | ".join(signal.reasoning), now.isoformat()))
            run_id = int(cursor.lastrowid)
            trade_row = connection.execute("SELECT id FROM demo_trades WHERE decision_id = ?", (decision_id,)).fetchone() if decision_id else None
            connection.execute("""INSERT INTO autonomous_experiences (run_id, symbol, regime, features_json, action, confidence, decision_id, trade_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (run_id, settings.autonomous_symbol, regime,
                json.dumps({"trend": analysis.trend.value, "trend_strength": analysis.trend_strength,
                            "market_intelligence": intelligence.model_dump(mode="json"),
                            "indicators": {item.name: item.value for item in analysis.indicators}}),
                signal.action.value, signal.confidence, decision_id, int(trade_row["id"]) if trade_row else None, now.isoformat()))
        return {"status": status, "candle_key": candle_key, "regime": regime, "action": signal.action.value,
                "confidence": signal.confidence, "decision_id": decision_id, "reasoning": signal.reasoning}

    def status(self) -> dict:
        self.sync_experiences()
        with demo_trading_service._connect() as connection:
            runs = connection.execute("SELECT * FROM autonomous_runs ORDER BY created_at DESC LIMIT 20").fetchall()
            count = connection.execute("SELECT COUNT(*) FROM autonomous_experiences").fetchone()[0]
        return {"enabled": settings.autonomous_trading_enabled, "symbol": settings.autonomous_symbol,
                "experience_count": count, "recent_runs": [dict(row) for row in runs]}

    def sync_experiences(self) -> int:
        """Convertit les trades clos en exemples étiquetés pour le futur entraînement."""
        now = self._now().isoformat()
        with demo_trading_service._connect() as connection:
            rows = connection.execute("""SELECT e.id, t.pnl_usdt FROM autonomous_experiences e
                JOIN demo_trades t ON t.id = e.trade_id
                WHERE e.outcome = 'pending' AND t.status = 'closed'""").fetchall()
            for row in rows:
                pnl = float(row["pnl_usdt"] or 0)
                outcome = "win" if pnl > 0 else "loss" if pnl < 0 else "flat"
                connection.execute("UPDATE autonomous_experiences SET pnl_usdt = ?, outcome = ?, resolved_at = ? WHERE id = ?",
                                   (pnl, outcome, now, row["id"]))
        return len(rows)


autonomous_trading_service = AutonomousTradingService()
