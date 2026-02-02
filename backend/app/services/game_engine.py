from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime
import uuid
import logging

from app.models.game_models import GameSession, GameRound, GameEvent
from app.models.sql_models import Player
from app.schemas.game_schemas import ProviderEvent, ProviderResponse
from app.services.wallet_ledger import apply_wallet_delta_with_ledger, spend_with_bonus_precedence
from app.services.bonus_engine import find_applicable_free_grant, consume_free_use
from app.core.errors import AppError

logger = logging.getLogger(__name__)

class GameEngine:
    """
    Core Logic for processing Game Events (Bet/Win) and syncing with Ledger.
    """
    
    @staticmethod
    async def process_event(session: AsyncSession, payload: ProviderEvent) -> ProviderResponse:
        # 1. Validate Session & Player
        game_session = await session.get(GameSession, payload.session_id)
        if not game_session:
            raise AppError("SESSION_NOT_FOUND", 404)
            
        player = await session.get(Player, game_session.player_id)
        if not player:
            raise AppError("PLAYER_NOT_FOUND", 404)
            
        # 2. Idempotency Check (GameEvent level)
        # Check if we already processed this provider_event_id
        stmt_exist = select(GameEvent).where(GameEvent.provider_event_id == payload.provider_event_id)
        existing_event = (await session.execute(stmt_exist)).scalars().first()
        
        if existing_event:
            logger.info(f"Idempotency hit for GameEvent {payload.provider_event_id}")
            # Return current balance without processing
            return ProviderResponse(
                balance=float(player.balance_real_available or 0.0) + float(player.balance_bonus or 0.0),
                currency=payload.currency,
                event_id=existing_event.id
            )

        # 3. Handle Round Lifecycle
        # Find or Create Round
        stmt_round = select(GameRound).where(
            GameRound.provider_round_id == payload.provider_round_id,
            GameRound.provider_round_id is not None # Safety
        )
        game_round = (await session.execute(stmt_round)).scalars().first()
        
        if not game_round:
            # New Round
            game_round = GameRound(
                tenant_id=game_session.tenant_id,
                player_id=player.id,
                session_id=game_session.id,
                game_id=game_session.game_id,
                provider_round_id=payload.provider_round_id,
                status="open"
            )
            session.add(game_round)
            await session.flush() # Get ID
            
        # 4. Apply wallet changes with P0-05 precedence rules
        tx_id = str(uuid.uuid4())
        ledger_type = f"game_{payload.event_type.lower()}"

        try:
            if payload.event_type == "BET":
                # P0-01/02: if player has an applicable free bet/spin for this game, consume a use and skip debit.
                game_id = payload.game_id or game_session.game_id
                free_grant = await find_applicable_free_grant(
                    session,
                    tenant_id=player.tenant_id,
                    player_id=player.id,
                    game_id=str(game_id),
                )

                if free_grant:
                    await consume_free_use(session, grant=free_grant, provider_event_id=payload.provider_event_id)
                    # Track bet volume but do not debit wallet.
                    game_round.total_bet += abs(payload.amount)
                else:
                    # Debit: bonus first then real
                    await spend_with_bonus_precedence(
                        session,
                        tenant_id=player.tenant_id,
                        player_id=player.id,
                        tx_id=tx_id,
                        event_type=ledger_type,
                        amount=float(abs(payload.amount)),
                        currency=payload.currency,
                        idempotency_key=f"game:{payload.provider_event_id}",
                        provider=payload.provider_id,
                        provider_ref=payload.provider_round_id,
                        provider_event_id=payload.provider_event_id,
                    )
                    game_round.total_bet += abs(payload.amount)

            elif payload.event_type == "WIN":
                # Bonus: Update Wagering Progress
                if player.wagering_remaining > 0:
                    player.wagering_remaining = max(0.0, player.wagering_remaining - abs(payload.amount))
                    session.add(player)

                await apply_wallet_delta_with_ledger(
                    session,
                    tenant_id=player.tenant_id,
                    player_id=player.id,
                    tx_id=tx_id,
                    event_type=ledger_type,
                    delta_available=float(abs(payload.amount)),
                    delta_held=0.0,
                    currency=payload.currency,
                    idempotency_key=f"game:{payload.provider_event_id}",
                    provider=payload.provider_id,
                    provider_ref=payload.provider_round_id,
                    provider_event_id=payload.provider_event_id,
                )
                game_round.total_win += abs(payload.amount)

            elif payload.event_type == "REFUND":
                await apply_wallet_delta_with_ledger(
                    session,
                    tenant_id=player.tenant_id,
                    player_id=player.id,
                    tx_id=tx_id,
                    event_type=ledger_type,
                    delta_available=float(abs(payload.amount)),
                    delta_held=0.0,
                    currency=payload.currency,
                    idempotency_key=f"game:{payload.provider_event_id}",
                    provider=payload.provider_id,
                    provider_ref=payload.provider_round_id,
                    provider_event_id=payload.provider_event_id,
                )
                game_round.total_bet -= abs(payload.amount)

        except Exception as e:
            logger.error(f"Ledger Error: {e}")
            if "went negative" in str(e) or "INSUFFICIENT_FUNDS" in str(e):
                raise AppError("INSUFFICIENT_FUNDS", 402)
            raise e

        # spend/apply functions are idempotent at the ledger level; nothing else required here.

        # 6. Record Game Event
        new_event = GameEvent(
            round_id=game_round.id,
            provider_event_id=payload.provider_event_id,
            type=payload.event_type,
            amount=payload.amount,
            currency=payload.currency,
            tx_id=tx_id
        )
        session.add(new_event)
        
        # 7. Update Session Activity
        game_session.last_activity_at = datetime.utcnow()
        session.add(game_session)
        
        await session.commit()
        await session.refresh(player)
        
        return ProviderResponse(
            balance=float(player.balance_real_available or 0.0) + float(player.balance_bonus or 0.0),
            currency=payload.currency,
            event_id=new_event.id
        )
