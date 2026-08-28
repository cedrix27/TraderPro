"""Persistent paper-trading journal backed by the local TraderPro SQLite database."""

import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.models import (
    DemoDecision,
    DemoHistoryResponse,
    DemoPosition,
    DemoTradeHistory,
    SignalType,
    TradingSignal,
)
from app.services.binance_service import binance_service


class DemoTradingService:
    """Records every decision and submits orders only to Binance Spot Testnet."""

    def __init__(self) -> None:
        database_path = settings.database_url.removeprefix("sqlite:///")
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS demo_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    amount_usdt REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rejection_reason TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS demo_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    amount_usdt REAL NOT NULL,
                    pnl_usdt REAL,
                    status TEXT NOT NULL,
                    is_testnet INTEGER NOT NULL DEFAULT 1,
                    binance_order_id TEXT,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    FOREIGN KEY(decision_id) REFERENCES demo_decisions(id)
                );
                CREATE INDEX IF NOT EXISTS ix_demo_decisions_created_at ON demo_decisions(created_at DESC);
                CREATE INDEX IF NOT EXISTS ix_demo_trades_status ON demo_trades(status);
                """
            )
            existing = {row[1] for row in connection.execute("PRAGMA table_info(demo_trades)")}
            for name, definition in {
                "leverage": "INTEGER NOT NULL DEFAULT 1",
                "margin_mode": "TEXT NOT NULL DEFAULT 'ISOLATED'",
                "liquidation_price": "REAL",
                "stop_loss": "REAL",
                "take_profit": "REAL",
                "stop_order_id": "TEXT",
                "take_profit_order_id": "TEXT",
            }.items():
                if name not in existing:
                    connection.execute(f"ALTER TABLE demo_trades ADD COLUMN {name} {definition}")
            connection.execute("UPDATE demo_trades SET side = 'LONG' WHERE side = 'BUY'")

    @staticmethod
    def _now() -> datetime:
        return datetime.now().astimezone()

    @staticmethod
    def _datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    def _store_decision(self, signal: TradingSignal, symbol: str, amount_usdt: float) -> int:
        now = self._now().isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO demo_decisions
                (symbol, action, confidence, amount_usdt, reasoning, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'recorded', ?)""",
                (symbol, signal.action.value, signal.confidence, amount_usdt, "\n".join(signal.reasoning), now),
            )
            return int(cursor.lastrowid)

    def _set_decision_status(self, decision_id: int, status: str, rejection_reason: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE demo_decisions SET status = ?, rejection_reason = ? WHERE id = ?",
                (status, rejection_reason, decision_id),
            )

    def _decision(self, decision_id: int) -> DemoDecision:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM demo_decisions WHERE id = ?", (decision_id,)).fetchone()
        if row is None:
            raise ValueError("Décision démo introuvable.")
        return self._to_decision(row)

    async def execute_signal(self, signal: TradingSignal, symbol: str, amount_usdt: float) -> DemoDecision:
        symbol = symbol.upper().strip()
        decision_id = self._store_decision(signal, symbol, amount_usdt)
        if signal.action == SignalType.HOLD:
            return self._decision(decision_id)

        try:
            open_trade = self._get_open_trade(symbol)
            if signal.action in {SignalType.BUY, SignalType.SELL} and open_trade is None:
                await binance_service.configure_futures_isolated_1x(symbol)
                mark_price = await binance_service.get_futures_mark_price(symbol)
                side, direction = ("BUY", "LONG") if signal.action == SignalType.BUY else ("SELL", "SHORT")
                order = await binance_service.create_futures_market_order(symbol, side, amount_usdt / mark_price)
                quantity = float(order.get("executedQty", 0))
                if quantity <= 0:
                    raise ValueError("Binance Testnet n'a retourné aucune quantité exécutée.")
                entry_price = float(order.get("avgPrice") or 0)
                quote_amount = float(order.get("cumQuote") or 0)
                if entry_price <= 0:
                    entry_price = (quote_amount / quantity) if quote_amount > 0 else mark_price
                if quote_amount <= 0:
                    quote_amount = entry_price * quantity
                try:
                    stop_order, take_profit_order = await binance_service.create_futures_protective_orders(symbol, side, signal.stop_loss, signal.take_profit)
                except ValueError as exc:
                    await binance_service.create_futures_market_order(symbol, "SELL" if side == "BUY" else "BUY", quantity, reduce_only=True)
                    raise ValueError(f"Protection SL/TP refusée ; position Testnet refermée : {exc}") from exc
                with self._connect() as connection:
                    connection.execute("""INSERT INTO demo_trades
                        (decision_id, symbol, side, quantity, entry_price, amount_usdt, status, binance_order_id, stop_loss, take_profit, stop_order_id, take_profit_order_id, opened_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)""",
                        (decision_id, symbol, direction, quantity, entry_price, quote_amount, str(order.get("orderId", "")), signal.stop_loss, signal.take_profit,
                         str(stop_order.get("algoId") or stop_order.get("orderId", "")), str(take_profit_order.get("algoId") or take_profit_order.get("orderId", "")), self._now().isoformat()))
            else:
                close_side = "SELL" if open_trade["side"] == "LONG" else "BUY"
                await binance_service.cancel_futures_order(symbol, str(open_trade["stop_order_id"] or ""))
                await binance_service.cancel_futures_order(symbol, str(open_trade["take_profit_order_id"] or ""))
                order = await binance_service.create_futures_market_order(symbol, close_side, float(open_trade["quantity"]), reduce_only=True)
                quantity = float(order.get("executedQty", 0))
                quote_amount = float(order.get("cumQuote", 0))
                if quantity <= 0:
                    raise ValueError("Fermeture Futures non exécutée.")
                exit_price = quote_amount / quantity
                direction = 1 if open_trade["side"] == "LONG" else -1
                pnl = (exit_price - float(open_trade["entry_price"])) * float(open_trade["quantity"]) * direction
                with self._connect() as connection:
                    connection.execute("UPDATE demo_trades SET exit_price = ?, pnl_usdt = ?, status = 'closed', closed_at = ? WHERE id = ?", (exit_price, pnl, self._now().isoformat(), open_trade["id"]))
            self._set_decision_status(decision_id, "executed")
        except ValueError as exc:
            self._set_decision_status(decision_id, "rejected", str(exc))

        return self._decision(decision_id)

    def _get_open_trade(self, symbol: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM demo_trades WHERE symbol = ? AND status = 'open' ORDER BY opened_at DESC LIMIT 1",
                (symbol,),
            ).fetchone()

    def _to_decision(self, row: sqlite3.Row) -> DemoDecision:
        return DemoDecision(
            id=row["id"], symbol=row["symbol"], action=row["action"], confidence=row["confidence"],
            amount_usdt=row["amount_usdt"], reasoning=row["reasoning"].split("\n"), status=row["status"],
            rejection_reason=row["rejection_reason"], created_at=self._datetime(row["created_at"]),
        )

    def _to_trade(self, row: sqlite3.Row) -> DemoTradeHistory:
        return DemoTradeHistory(
            id=row["id"], decision_id=row["decision_id"], symbol=row["symbol"], side=("LONG" if row["side"] == "BUY" else row["side"]),
            quantity=row["quantity"], entry_price=row["entry_price"], exit_price=row["exit_price"],
            amount_usdt=row["amount_usdt"], pnl_usdt=row["pnl_usdt"], status=row["status"],
            is_testnet=bool(row["is_testnet"]), leverage=row["leverage"], margin_mode=row["margin_mode"], liquidation_price=row["liquidation_price"], opened_at=self._datetime(row["opened_at"]),
            closed_at=self._datetime(row["closed_at"]),
        )

    async def history(self) -> DemoHistoryResponse:
        with self._connect() as connection:
            decision_rows = connection.execute("SELECT * FROM demo_decisions ORDER BY created_at DESC LIMIT 100").fetchall()
            trade_rows = connection.execute("SELECT * FROM demo_trades ORDER BY opened_at DESC LIMIT 100").fetchall()
        open_positions: list[DemoPosition] = []
        for row in trade_rows:
            if row["status"] != "open":
                continue
            current_price = None
            pnl = None
            try:
                current_price = await binance_service.get_futures_mark_price(row["symbol"])
                direction = 1 if row["side"] == "LONG" else -1
                pnl = (current_price - float(row["entry_price"])) * float(row["quantity"]) * direction
            except Exception:
                pass
            open_positions.append(DemoPosition(
                id=row["id"], decision_id=row["decision_id"], symbol=row["symbol"], side=("LONG" if row["side"] == "BUY" else row["side"]),
                quantity=row["quantity"], entry_price=row["entry_price"], amount_usdt=row["amount_usdt"],
                current_price=current_price, unrealized_pnl_usdt=pnl, opened_at=self._datetime(row["opened_at"]),
            ))
        trades = [self._to_trade(row) for row in trade_rows]
        realized_pnl = sum(trade.pnl_usdt or 0 for trade in trades if trade.status == "closed")
        return DemoHistoryResponse(
            mode="binance_usdt_m_futures_testnet", decisions=[self._to_decision(row) for row in decision_rows],
            open_positions=open_positions, trades=trades, realized_pnl_usdt=realized_pnl,
        )


demo_trading_service = DemoTradingService()
