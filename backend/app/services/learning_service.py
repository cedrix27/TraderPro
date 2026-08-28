"""Champion/challenger registry for controlled strategy improvements."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.services.demo_trading_service import demo_trading_service


class LearningService:
    PROMOTION_CRITERIA = {
        "minimum_resolved_experiences": 100,
        "minimum_profit_factor": 1.15,
        "minimum_net_pnl_usdt": 0.0,
        "maximum_drawdown_ratio": 0.15,
        "required_fresh_walk_forward_windows": 3,
    }
    def initialize(self) -> None:
        with demo_trading_service._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    artifact_path TEXT,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    promoted_at TEXT
                );
            """)
            exists = connection.execute("SELECT 1 FROM model_registry WHERE role = 'champion'").fetchone()
            if not exists:
                connection.execute("""INSERT INTO model_registry (name, version, role, metrics_json, created_at, promoted_at)
                    VALUES (?, ?, 'champion', ?, ?, ?)""", ("adaptive_regime_rules", "rules-v1", "{}", self._now(), self._now()))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def experience_summary(self) -> dict[str, Any]:
        with demo_trading_service._connect() as connection:
            row = connection.execute("""SELECT COUNT(*) AS total,
                SUM(CASE WHEN outcome != 'pending' THEN 1 ELSE 0 END) AS resolved,
                COALESCE(SUM(pnl_usdt), 0) AS pnl,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) AS losses
                FROM autonomous_experiences""").fetchone()
        resolved, wins, losses = int(row["resolved"] or 0), int(row["wins"] or 0), int(row["losses"] or 0)
        return {"total": int(row["total"] or 0), "resolved": resolved, "net_pnl_usdt": float(row["pnl"] or 0),
                "win_rate": wins / resolved if resolved else None,
                "ready_for_challenger_training": resolved >= 100,
                "minimum_resolved_experiences": 100,
                "wins": wins, "losses": losses}

    def status(self) -> dict[str, Any]:
        with demo_trading_service._connect() as connection:
            models = connection.execute("SELECT * FROM model_registry ORDER BY created_at DESC").fetchall()
        return {"experience_summary": self.experience_summary(), "promotion_criteria": self.PROMOTION_CRITERIA, "models": [
            {**dict(row), "metrics": json.loads(row["metrics_json"])} for row in models
        ]}


learning_service = LearningService()
