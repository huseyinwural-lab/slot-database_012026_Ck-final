from typing import List, Dict, Optional
import random
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.game_models import GameSession, Game, GameRound
from app.models.robot_models import GameRobotBinding, RobotDefinition, MathAsset
from app.core.errors import AppError

class SlotMath:
    
    @staticmethod
    async def load_context(session: AsyncSession, game_session: GameSession):
        # 1. Find Binding
        stmt = select(GameRobotBinding).where(
            GameRobotBinding.game_id == game_session.game_id,
            GameRobotBinding.is_enabled
        ).order_by(GameRobotBinding.created_at.desc())
        
        binding = (await session.execute(stmt)).scalars().first()
        if not binding:
            raise AppError("ROBOT_NOT_BOUND", 409)
            
        # 2. Load Robot
        robot = await session.get(RobotDefinition, binding.robot_id)
        if not robot or not robot.is_active:
            raise AppError("ROBOT_DISABLED", 409)
            
        # 3. Load Assets
        config = robot.config
        pay_ref = config.get("paytable_ref")
        reel_ref = config.get("reelset_ref")
        
        assets = {}
        for ref in [pay_ref, reel_ref]:
            if not ref: continue
            stmt_asset = select(MathAsset).where(MathAsset.ref_key == ref)
            asset = (await session.execute(stmt_asset)).scalars().first()
            if not asset:
                raise AppError(f"MISSING_ASSET: {ref}", 500)
            assets[asset.type] = asset
            
        return robot, assets.get("reelset"), assets.get("paytable")

    @staticmethod
    def generate_grid(reelset_content: Dict, seed: str) -> List[List[int]]:
        """
        Deterministic Grid Generation.
        Input: Reelset { "reels": [[0,1,2...], ...] }
        Output: 3x5 Grid (3 rows, 5 cols) - Transposed from 5 reels
        """
        reels = reelset_content.get("reels", [])
        if not reels:
            raise AppError("INVALID_REELSET", 500)
            
        # Initialize RNG with Seed
        # Python random is Mersenne Twister, not strictly crypto-secure but deterministic with seed.
        # For gambling, we'd use a CSPRNG, but this suffices for 'Controlled Casino' simulation.
        rng = random.Random(seed)
        
        grid = []
        # Assumption: Standard 5 Reel, 3 Row
        # Output format: rows
        # Row 0: [R1_0, R2_0, R3_0, R4_0, R5_0]
        # Row 1: [R1_1, R2_1, R3_1, R4_1, R5_1]
        # Row 2: ...
        
        # Stops
        stops = []
        
        num_reels = len(reels) # Should be 3 for Classic 777 MVP, or 5
        rows = 3
        
        # Build columns first
        cols = []
        for i in range(num_reels):
            strip = reels[i]
            length = len(strip)
            stop = rng.randint(0, length - 1)
            stops.append(stop)
            
            col_symbols = []
            for r in range(rows):
                idx = (stop + r) % length
                col_symbols.append(strip[idx])
            cols.append(col_symbols)
            
        # Transpose to Rows
        grid_rows = []
        for r in range(rows):
            row_data = []
            for c in range(num_reels):
                row_data.append(cols[c][r])
            grid_rows.append(row_data)
            
        return grid_rows, stops

    @staticmethod
    def calculate_payout(grid: List[List[int]], paytable_content: Dict, bet_amount: float) -> Dict:
        """
        MVP Payout: Center Line Only.
        """
        # 3x3 for Classic 777
        # Center Line is Row 1 (index 1)
        center_row = grid[1]
        
        payouts = paytable_content
        # Format: { "0": 5, "1": 10 ... } (Symbol ID -> Multiplier for 3 match)
        
        # Check match
        first = center_row[0]
        match_count = 1
        for i in range(1, len(center_row)):
            if center_row[i] == first:
                match_count += 1
            else:
                break
        
        win_amount = 0.0
        win_details = []
        
        # Simplistic: Only pays on full match of 3 (since it's 3 reels)
        # Or match_count >= X
        if match_count == len(center_row):
            symbol_key = str(first)
            multiplier = payouts.get(symbol_key, 0)
            if multiplier > 0:
                win_amount = bet_amount * multiplier
                win_details.append({
                    "line": 1, 
                    "symbol": first, 
                    "count": match_count, 
                    "multiplier": multiplier, 
                    "amount": win_amount
                })
                
        return {
            "total_win": win_amount,
            "details": win_details
        }
