import json
import logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from redis.asyncio import Redis

from app.models.risk import RiskProfile, RiskLevel
from app.core.config import settings

logger = logging.getLogger(__name__)

class RiskService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        
    async def process_event(self, event_type: str, user_id: str, tenant_id: str, payload: dict):
        """
        Ingests a risk event, updates velocity, and recalculates score.
        This is fire-and-forget mostly, but persists critical changes.
        """
        try:
            # 1. Update Velocity
            await self._update_velocity(event_type, user_id, payload)
            
            # 2. Get Profile
            profile = await self._get_or_create_profile(user_id, tenant_id)
            
            # 3. Apply Rules
            delta_score = await self._evaluate_rules(event_type, user_id, payload, profile)
            
            if delta_score != 0:
                profile.risk_score = max(0, min(100, profile.risk_score + delta_score))
                profile.risk_level = self._map_score_to_level(profile.risk_score)
                profile.last_event_at = datetime.utcnow()
                self.db.add(profile)
                await self.db.commit()
                
                logger.info(f"Risk score updated: user={user_id} score={profile.risk_score} level={profile.risk_level}")
                
        except Exception as e:
            logger.error(f"Risk processing failed: {e}")
            # Non-blocking, but logged
            
    async def evaluate_withdrawal(self, user_id: str, amount: float) -> str:
        """
        Guard method for Withdrawal Service.
        Returns: 'ALLOW', 'FLAG', 'BLOCK'
        """
        try:
            # 1. Get Profile
            stmt = select(RiskProfile).where(RiskProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            profile = result.scalars().first()
            
            if not profile:
                # Default safety: New users without history are treated cautiously but allowed if no other signals
                return "ALLOW" # Or FLAG if strictly paranoid
                
            # 2. Hard Block Checks
            if profile.risk_score >= 70:
                return "BLOCK"
                
            # 3. Soft Flag Checks
            if profile.risk_score >= 40:
                return "FLAG"
                
            # 4. Velocity Check (Withdrawal Specific)
            # Check 24h limit
            w_key = f"risk:velocity:wdraw_amt:{user_id}:86400"
            current_24h = await self.redis.get(w_key)
            if current_24h and (float(current_24h) + amount) > 5000:
                return "FLAG" # Velocity limit hit
                
            return "ALLOW"
            
        except Exception as e:
            logger.error(f"Risk evaluation failed: {e}")
            return "FLAG" # Fail-Safe

    async def _update_velocity(self, event_type: str, user_id: str, payload: dict):
        pipe = self.redis.pipeline()
        
        if event_type == "DEPOSIT_REQUESTED":
            # Count 10m
            key = f"risk:velocity:dep_count:{user_id}:600"
            pipe.incr(key)
            pipe.expire(key, 600, nx=True)
            
            # Amount 24h
            amt = payload.get("amount", 0)
            key_amt = f"risk:velocity:dep_amt:{user_id}:86400"
            pipe.incrbyfloat(key_amt, amt)
            pipe.expire(key_amt, 86400, nx=True)
            
        elif event_type == "WITHDRAW_REQUESTED":
            # Count 1h
            key = f"risk:velocity:wdraw_count:{user_id}:3600"
            pipe.incr(key)
            pipe.expire(key, 3600, nx=True)
            
            # Amount 24h
            amt = payload.get("amount", 0)
            key_amt = f"risk:velocity:wdraw_amt:{user_id}:86400"
            pipe.incrbyfloat(key_amt, amt)
            pipe.expire(key_amt, 86400, nx=True)
            
        await pipe.execute()

    async def _evaluate_rules(self, event_type: str, user_id: str, payload: dict, profile: RiskProfile) -> int:
        score = 0
        
        if event_type == "DEPOSIT_REQUESTED":
            # Rule: Rapid Deposit (>3 in 10m)
            key = f"risk:velocity:dep_count:{user_id}:600"
            val = await self.redis.get(key)
            if val and int(val) > 3:
                score += 30
                
        elif event_type == "WITHDRAW_REQUESTED":
            # Rule: Rapid Withdraw (>2 in 1h)
            key = f"risk:velocity:wdraw_count:{user_id}:3600"
            val = await self.redis.get(key)
            if val and int(val) > 2:
                score += 20
                
            # Rule: Churn (Withdraw shortly after Deposit?)
            # Requires last_deposit_at tracking in profile or Redis. Skipping for simple Sprint 1.

        return score

    async def _get_or_create_profile(self, user_id: str, tenant_id: str) -> RiskProfile:
        stmt = select(RiskProfile).where(RiskProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalars().first()
        
        if not profile:
            profile = RiskProfile(user_id=user_id, tenant_id=tenant_id)
            self.db.add(profile)
            # Commit logic is handled by caller or flush here
            await self.db.flush()
            
        return profile

    def _map_score_to_level(self, score: int) -> RiskLevel:
        if score >= 70:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
