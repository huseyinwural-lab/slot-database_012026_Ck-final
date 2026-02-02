from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import hashlib

from app.models.offer_models import Experiment, ExperimentAssignment

class ExperimentEngine:
    
    async def get_assignment(self, session: AsyncSession, tenant_id: str, player_id: str, experiment_key: str) -> str:
        """
        Get or Create Sticky Assignment.
        Deterministic: Hashing (player_id + key) if no override.
        """
        
        # 1. Check Active Experiment
        stmt = select(Experiment).where(Experiment.tenant_id == tenant_id, Experiment.key == experiment_key)
        experiment = (await session.execute(stmt)).scalars().first()
        
        if not experiment or experiment.status != "running":
            return "control" # Default fallback
            
        # 2. Check Existing Assignment
        stmt_assign = select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment.id,
            ExperimentAssignment.player_id == player_id
        )
        assignment = (await session.execute(stmt_assign)).scalars().first()
        
        if assignment:
            return assignment.variant
            
        # 3. Create New Assignment (Deterministic)
        variant = self._assign_variant(player_id, experiment)
        
        new_assign = ExperimentAssignment(
            tenant_id=tenant_id,
            experiment_id=experiment.id,
            player_id=player_id,
            variant=variant
        )
        session.add(new_assign)
        # We rely on caller to commit to make it sticky
        return variant

    def _assign_variant(self, player_id: str, experiment: Experiment) -> str:
        # Simple Weighted Random logic using Hash
        # Variants: {"A": 50, "B": 50}
        
        if not experiment.variants:
            return "control"
            
        variants = experiment.variants
        total_weight = sum(v.get("weight", 0) for v in variants.values())
        if total_weight == 0:
            return "control"
            
        # Hash: MD5(player_id + key) -> Int -> Modulo Total Weight
        hash_input = f"{player_id}:{experiment.key}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        point = hash_val % total_weight
        
        current = 0
        for v_name, v_data in variants.items():
            current += v_data.get("weight", 0)
            if point < current:
                return v_name
                
        return "control"
