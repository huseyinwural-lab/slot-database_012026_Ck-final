from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.game_models import GameRound, GameEvent, Game, GameSession
from app.models.sql_models import Player
from app.services.wallet_ledger import (
    apply_wallet_delta_with_ledger,
    WalletInvariantError,
    spend_with_bonus_precedence,
)
from app.core.errors import AppError

logger = logging.getLogger(__name__)

class GameEngine:
    """Core logic for processing Game Events (Bet, Win, Rollback)."""

    async def process_bet(
        self,
        session: AsyncSession,
        provider: str,
        provider_tx_id: str,
        player_id: str,
        game_id: str,
        round_id: str,
        amount: float,
        currency: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Process a Debit (Bet)."""
        
        # 1. Idempotency Check (Fast Path)
        stmt = select(GameEvent).where(GameEvent.provider_event_id == provider_tx_id)
        existing_event = (await session.execute(stmt)).scalars().first()
        
        if existing_event:
            return await self._get_wallet_snapshot(session, player_id, currency)

        # 2. Validate
        game = await session.get(Game, game_id)
        if not game:
            # Fallback for "Simulator" game if not seeded
            if provider == "simulator":
                # Create ad-hoc game for sim
                game = Game(id=game_id, tenant_id="default_casino", provider_id="simulator", external_id=game_id, name="Sim Game")
                session.add(game)
                await session.flush()
            else:
                raise AppError("GAME_NOT_FOUND", status_code=404)

        # 3. Upsert Round
        stmt_round = select(GameRound).where(
            GameRound.provider_round_id == round_id, 
            GameRound.game_id == game_id
        )
        round_obj = (await session.execute(stmt_round)).scalars().first()
        
        if not round_obj:
            round_obj = GameRound(
                id=str(uuid.uuid4()),
                tenant_id=game.tenant_id,
                player_id=player_id,
                session_id=str(uuid.uuid4()), 
                game_id=game_id,
                provider_round_id=round_id,
                status="open",
                total_bet=0.0,
                total_win=0.0,
            )
            session.add(round_obj)
            await session.flush()

        # 4. Wallet Debit
        tx_id = str(uuid.uuid4())
        try:
            success = await spend_with_bonus_precedence(
                session,
                tenant_id=game.tenant_id,
                player_id=player_id,
                tx_id=tx_id,
                event_type="game_bet",
                amount=amount,
                currency=currency,
                idempotency_key=provider_tx_id, 
                provider=provider,
                provider_event_id=provider_tx_id,
            )
        except WalletInvariantError as e:
            raise AppError("INSUFFICIENT_FUNDS", status_code=402, message=str(e))

        if not success:
            return await self._get_wallet_snapshot(session, player_id, currency)

        # 5. Record Game Event
        event = GameEvent(
            round_id=round_obj.id,
            provider_event_id=provider_tx_id,
            type="BET",
            amount=amount,
            currency=currency,
            tx_id=tx_id
        )
        session.add(event)
        
        # Update Round Totals
        round_obj.total_bet += amount
        session.add(round_obj)
        
        return await self._get_wallet_snapshot(session, player_id, currency)

    async def process_win(
        self,
        session: AsyncSession,
        provider: str,
        provider_tx_id: str,
        player_id: str,
        game_id: str,
        round_id: str,
        amount: float,
        currency: str,
        is_round_complete: bool = False,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Process a Credit (Win)."""
        
        stmt = select(GameEvent).where(GameEvent.provider_event_id == provider_tx_id)
        existing_event = (await session.execute(stmt)).scalars().first()
        if existing_event:
            return await self._get_wallet_snapshot(session, player_id, currency)

        game = await session.get(Game, game_id)
        if not game:
             if provider == "simulator":
                game = Game(id=game_id, tenant_id="default_casino", provider_id="simulator", external_id=game_id, name="Sim Game")
                session.add(game)
                await session.flush()
             else:
                raise AppError("GAME_NOT_FOUND", status_code=404)

        stmt_round = select(GameRound).where(
            GameRound.provider_round_id == round_id, 
            GameRound.game_id == game_id
        )
        round_obj = (await session.execute(stmt_round)).scalars().first()
        
        if not round_obj:
             round_obj = GameRound(
                id=str(uuid.uuid4()),
                tenant_id=game.tenant_id,
                player_id=player_id,
                session_id=str(uuid.uuid4()),
                game_id=game_id,
                provider_round_id=round_id,
                status="open",
            )
             session.add(round_obj)
             await session.flush()

        tx_id = str(uuid.uuid4())
        
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=game.tenant_id,
            player_id=player_id,
            tx_id=tx_id,
            event_type="game_win",
            delta_available=amount,
            delta_held=0.0,
            currency=currency,
            idempotency_key=provider_tx_id,
            provider=provider,
            provider_event_id=provider_tx_id,
        )

        event = GameEvent(
            round_id=round_obj.id,
            provider_event_id=provider_tx_id,
            type="WIN",
            amount=amount,
            currency=currency,
            tx_id=tx_id
        )
        session.add(event)
        
        round_obj.total_win += amount
        if is_round_complete:
            round_obj.status = "closed"
        session.add(round_obj)

        return await self._get_wallet_snapshot(session, player_id, currency)

    async def process_rollback(
        self,
        session: AsyncSession,
        provider: str,
        provider_tx_id: str,
        ref_provider_tx_id: str,
        player_id: str,
        game_id: str,
        round_id: str,
        amount: Optional[float] = None,
        currency: str = "USD",
    ) -> Dict:
        """Process a Rollback."""
        
        stmt = select(GameEvent).where(GameEvent.provider_event_id == provider_tx_id)
        if (await session.execute(stmt)).scalars().first():
            return await self._get_wallet_snapshot(session, player_id, currency)

        stmt_ref = select(GameEvent).where(GameEvent.provider_event_id == ref_provider_tx_id)
        ref_event = (await session.execute(stmt_ref)).scalars().first()
        
        if not ref_event:
            # Assume OK to avoid deadlock
            return await self._get_wallet_snapshot(session, player_id, currency)

        rollback_amount = amount if amount is not None else ref_event.amount
        
        tx_id = str(uuid.uuid4())
        game = await session.get(Game, game_id)
        # Handle fallback for sim if game deleted
        tenant_id = game.tenant_id if game else "default_casino"

        if ref_event.type == "BET":
            await apply_wallet_delta_with_ledger(
                session,
                tenant_id=tenant_id,
                player_id=player_id,
                tx_id=tx_id,
                event_type="game_rollback_bet",
                delta_available=rollback_amount,
                delta_held=0.0,
                currency=currency,
                idempotency_key=provider_tx_id,
                provider=provider,
                provider_event_id=provider_tx_id,
            )
        elif ref_event.type == "WIN":
            await apply_wallet_delta_with_ledger(
                session,
                tenant_id=tenant_id,
                player_id=player_id,
                tx_id=tx_id,
                event_type="game_rollback_win",
                delta_available=-rollback_amount,
                delta_held=0.0,
                currency=currency,
                idempotency_key=provider_tx_id,
                provider=provider,
                provider_event_id=provider_tx_id,
                allow_negative=True, 
            )

        event = GameEvent(
            round_id=ref_event.round_id,
            provider_event_id=provider_tx_id,
            type="ROLLBACK",
            amount=rollback_amount,
            currency=currency,
            tx_id=tx_id
        )
        session.add(event)
        
        return await self._get_wallet_snapshot(session, player_id, currency)

    async def _get_wallet_snapshot(self, session: AsyncSession, player_id: str, currency: str) -> Dict:
        player = await session.get(Player, player_id)
        return {
            "balance": float(player.balance_real_available),
            "currency": currency
        }

game_engine = GameEngine()
