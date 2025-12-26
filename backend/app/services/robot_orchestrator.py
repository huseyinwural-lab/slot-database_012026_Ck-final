from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.game_models import Game

SUPPORTED_GAME_TYPES = {"slot", "crash", "dice"}
MAX_ROUNDS_PER_TYPE = 1000
MAX_TOTAL_WORK = 5000  # len(game_types) * rounds


@dataclass
class ScenarioSummary:
    game_type: str
    game_id: Optional[str]
    rounds: int
    errors: int
    avg_rtp: Optional[float]
    avg_duration_ms: Optional[float]


class RobotOrchestrator:
    """Robot orchestrator (SQLModel).

    This service is fully migrated to PostgreSQL/SQLModel.
    """

    def __init__(self, session: AsyncSession, http_client: httpx.AsyncClient):
        self.session = session
        self.http = http_client

    async def run_rounds(
        self,
        tenant_id: str,
        game_types: List[str],
        rounds: int,
    ) -> Dict[str, Any]:
        if rounds < 1 or rounds > MAX_ROUNDS_PER_TYPE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": "ROBOT_ROUNDS_LIMIT_EXCEEDED", "rounds": rounds},
            )

        normalized_types = [g.strip().lower() for g in game_types if g.strip()]
        if not normalized_types:
            normalized_types = ["slot"]

        for g in normalized_types:
            if g not in SUPPORTED_GAME_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error_code": "ROBOT_GAME_TYPE_UNSUPPORTED", "game_type": g},
                )

        total_work = len(normalized_types) * rounds
        if total_work > MAX_TOTAL_WORK:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "ROBOT_TOTAL_WORK_EXCEEDED",
                    "total_work": total_work,
                    "max_total_work": MAX_TOTAL_WORK,
                },
            )

        results: List[ScenarioSummary] = []

        for g in normalized_types:
            if g == "slot":
                res = await self._run_slot_rounds(tenant_id, rounds)
            elif g == "crash":
                res = await self._run_crash_rounds(tenant_id, rounds)
            elif g == "dice":
                res = await self._run_dice_rounds(tenant_id, rounds)
            else:  # pragma: no cover
                continue
            results.append(res)

        return {
            "tenant_id": tenant_id,
            "total_rounds": sum(r.rounds for r in results),
            "results": [r.__dict__ for r in results],
        }

    async def _find_test_game(self, tenant_id: str, game_type: str) -> Optional[Game]:
        # Simple approach: find a game matching tenant + category
        stmt = select(Game).where(Game.tenant_id == tenant_id, Game.category == game_type.capitalize())
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def _run_slot_rounds(self, tenant_id: str, rounds: int) -> ScenarioSummary:
        game = await self._find_test_game(tenant_id, "slot")
        game_id = game.id if game else None

        if not game_id:
            return ScenarioSummary("slot", None, 0, 1, None, None)

        url = f"/api/v1/games/{game_id}/config/slot-advanced"
        errors = 0
        durations: List[float] = []

        for _ in range(rounds):
            start = datetime.now()
            try:
                resp = await self.http.get(url)
                if resp.status_code < 200 or resp.status_code >= 300:
                    errors += 1
            except Exception:
                errors += 1
            finally:
                end = datetime.now()
                durations.append((end - start).total_seconds() * 1000)

        avg_duration = sum(durations) / len(durations) if durations else None
        return ScenarioSummary("slot", game_id, rounds, errors, None, avg_duration)

    async def _run_crash_rounds(self, tenant_id: str, rounds: int) -> ScenarioSummary:
        game = await self._find_test_game(tenant_id, "crash")
        game_id = game.id if game else None

        if not game_id:
            return ScenarioSummary("crash", None, 0, 1, None, None)

        base_url = f"/api/v1/games/{game_id}/config/crash-math"
        errors = 0
        durations: List[float] = []

        base_cfg: Optional[Dict[str, Any]] = None
        try:
            base_resp = await self.http.get(base_url)
            if 200 <= base_resp.status_code < 300:
                base_cfg = base_resp.json()
        except Exception:
            base_cfg = None

        if not base_cfg:
            return ScenarioSummary("crash", game_id, 0, 1, None, None)

        for _ in range(rounds):
            payload = {
                "base_rtp": base_cfg.get("base_rtp", 96.0),
                "volatility_profile": base_cfg.get("volatility_profile", "medium"),
                "min_multiplier": base_cfg.get("min_multiplier", 1.0),
                "max_multiplier": base_cfg.get("max_multiplier", 500.0),
                "max_auto_cashout": base_cfg.get("max_auto_cashout", 100.0),
                "round_duration_seconds": base_cfg.get("round_duration_seconds", 12),
                "bet_phase_seconds": base_cfg.get("bet_phase_seconds", 6),
                "grace_period_seconds": base_cfg.get("grace_period_seconds", 2),
                "min_bet_per_round": base_cfg.get("min_bet_per_round"),
                "max_bet_per_round": base_cfg.get("max_bet_per_round"),
                "max_loss_per_round": base_cfg.get("max_loss_per_round"),
                "max_win_per_round": base_cfg.get("max_win_per_round"),
                "max_rounds_per_session": base_cfg.get("max_rounds_per_session"),
                "max_total_loss_per_session": base_cfg.get("max_total_loss_per_session"),
                "max_total_win_per_session": base_cfg.get("max_total_win_per_session"),
                "enforcement_mode": base_cfg.get("enforcement_mode", "log_only"),
                "country_overrides": base_cfg.get("country_overrides"),
                "provably_fair_enabled": base_cfg.get("provably_fair_enabled", True),
                "rng_algorithm": base_cfg.get("rng_algorithm", "sha256_chain"),
                "seed_rotation_interval_rounds": base_cfg.get("seed_rotation_interval_rounds"),
                "summary": "robot_round",
            }

            start = datetime.now()
            try:
                resp = await self.http.post(base_url, json=payload)
                if resp.status_code < 200 or resp.status_code >= 300:
                    errors += 1
            except Exception:
                errors += 1
            finally:
                end = datetime.now()
                durations.append((end - start).total_seconds() * 1000)

        avg_duration = sum(durations) / len(durations) if durations else None
        return ScenarioSummary("crash", game_id, rounds, errors, None, avg_duration)

    async def _run_dice_rounds(self, tenant_id: str, rounds: int) -> ScenarioSummary:
        game = await self._find_test_game(tenant_id, "dice")
        game_id = game.id if game else None

        if not game_id:
            return ScenarioSummary("dice", None, 0, 1, None, None)

        base_url = f"/api/v1/games/{game_id}/config/dice-math"
        errors = 0
        durations: List[float] = []

        base_cfg: Optional[Dict[str, Any]] = None
        try:
            base_resp = await self.http.get(base_url)
            if 200 <= base_resp.status_code < 300:
                base_cfg = base_resp.json()
        except Exception:
            base_cfg = None

        if not base_cfg:
            return ScenarioSummary("dice", game_id, 0, 1, None, None)

        for _ in range(rounds):
            payload = {
                "range_min": base_cfg.get("range_min", 0.0),
                "range_max": base_cfg.get("range_max", 99.99),
                "step": base_cfg.get("step", 0.01),
                "house_edge_percent": base_cfg.get("house_edge_percent", 1.0),
                "min_payout_multiplier": base_cfg.get("min_payout_multiplier", 1.01),
                "max_payout_multiplier": base_cfg.get("max_payout_multiplier", 990.0),
                "allow_over": base_cfg.get("allow_over", True),
                "allow_under": base_cfg.get("allow_under", True),
                "min_target": base_cfg.get("min_target", 1.0),
                "max_target": base_cfg.get("max_target", 98.0),
                "round_duration_seconds": base_cfg.get("round_duration_seconds", 5),
                "bet_phase_seconds": base_cfg.get("bet_phase_seconds", 3),
                "max_win_per_bet": base_cfg.get("max_win_per_bet"),
                "max_loss_per_bet": base_cfg.get("max_loss_per_bet"),
                "max_session_loss": base_cfg.get("max_session_loss"),
                "max_session_bets": base_cfg.get("max_session_bets"),
                "enforcement_mode": base_cfg.get("enforcement_mode", "log_only"),
                "country_overrides": base_cfg.get("country_overrides"),
                "provably_fair_enabled": base_cfg.get("provably_fair_enabled", True),
                "rng_algorithm": base_cfg.get("rng_algorithm", "sha256_chain"),
                "seed_rotation_interval_rounds": base_cfg.get("seed_rotation_interval_rounds"),
                "summary": "robot_round",
            }

            start = datetime.now()
            try:
                resp = await self.http.post(base_url, json=payload)
                if resp.status_code < 200 or resp.status_code >= 300:
                    errors += 1
            except Exception:
                errors += 1
            finally:
                end = datetime.now()
                durations.append((end - start).total_seconds() * 1000)

        avg_duration = sum(durations) / len(durations) if durations else None
        return ScenarioSummary("dice", game_id, rounds, errors, None, avg_duration)
