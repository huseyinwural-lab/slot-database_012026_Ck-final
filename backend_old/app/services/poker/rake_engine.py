from decimal import Decimal, ROUND_HALF_UP
from app.models.poker_models import RakeProfile

class RakeEngine:
    @staticmethod
    def calculate_rake(pot: float, profile: RakeProfile, player_count: int = 2) -> float:
        """
        Calculate rake based on Pot size and Profile rules.
        """
        if pot <= 0:
            return 0.0
            
        # 1. Base Percentage
        raw_rake = (pot * profile.percentage) / 100.0
        
        # 2. Apply Cap based on player count rules if any
        # Rule format: rules = { "2": 1.0, "3+": 3.0 } or similar logic
        # For MVP, we stick to global cap
        cap = profile.cap
        
        # Override cap if specific rule exists for player count
        # Assuming rules keys are string integers e.g. "2", "3", "4", "5+"
        if str(player_count) in profile.rules:
            cap = float(profile.rules[str(player_count)])
        
        # 3. Final calculation
        final_rake = min(raw_rake, cap)
        
        # Rounding (2 decimal places)
        return float(Decimal(str(final_rake)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_rakeback(rake_paid: float, rakeback_percentage: float) -> float:
        """Calculate rakeback for a player."""
        return float(Decimal(str(rake_paid * (rakeback_percentage / 100.0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

rake_engine = RakeEngine()
