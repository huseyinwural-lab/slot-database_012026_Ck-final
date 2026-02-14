import random
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

class SlotResult(BaseModel):
    grid: List[List[str]]
    stops: List[int]
    line_wins: List[Dict[str, Any]]
    total_win: float
    is_scatter_trigger: bool
    scatter_count: int

class SlotMathEngine:
    """
    Deterministic Slot Engine v1 (Payline).
    Supports:
    - Standard 5x3 Grid
    - Payline evaluation
    - Wild substitution
    - Scatter counts
    """

    def __init__(self, reels: List[List[str]], paytable: Dict[str, Dict[int, float]], lines: List[List[int]], wild_symbol: str = "WILD", scatter_symbol: str = "SCATTER"):
        self.reels = reels
        self.paytable = paytable
        self.lines = lines
        self.wild_symbol = wild_symbol
        self.scatter_symbol = scatter_symbol
        self.reel_count = len(reels)
        self.rows = 3 # Standard

    def spin(self, seed: str, total_bet: float) -> SlotResult:
        # 1. RNG & Grid Generation
        # Use local Random instance for thread-safety and determinism
        rng = random.Random(seed)
        
        stops = []
        grid = []
        
        # Transpose logic: Grid is Row x Col usually, but reels are Col-based.
        # Let's build Cols first then transpose.
        cols = []
        for i in range(self.reel_count):
            strip_len = len(self.reels[i])
            stop = rng.randint(0, strip_len - 1)
            stops.append(stop)
            
            # Extract visible window (handling wrap-around)
            col_symbols = []
            for r in range(self.rows):
                idx = (stop + r) % strip_len
                col_symbols.append(self.reels[i][idx])
            cols.append(col_symbols)
            
        # Grid: [Row][Col]
        grid = [[cols[c][r] for c in range(self.reel_count)] for r in range(self.rows)]
        
        # 2. Evaluation
        line_wins = []
        total_payout = 0.0
        line_bet = total_bet / len(self.lines) if self.lines else 0
        
        for line_idx, line_def in enumerate(self.lines):
            # Get symbols for this line
            # line_def is like [1, 1, 1, 1, 1] (row indices for each col)
            # or [0, 1, 2, 1, 0] (V shape)
            symbols = []
            for col_idx, row_idx in enumerate(line_def):
                if col_idx < self.reel_count:
                    symbols.append(grid[row_idx][col_idx])
            
            # Analyze line match
            match_sym, count, multiplier = self._evaluate_line(symbols)
            
            if multiplier > 0:
                win_amount = line_bet * multiplier
                line_wins.append({
                    "line_index": line_idx,
                    "symbol": match_sym,
                    "count": count,
                    "multiplier": multiplier,
                    "amount": win_amount
                })
                total_payout += win_amount

        # 3. Scatters
        scatter_count = sum(row.count(self.scatter_symbol) for row in grid)
        is_trigger = scatter_count >= 3 # Convention

        return SlotResult(
            grid=grid,
            stops=stops,
            line_wins=line_wins,
            total_win=total_payout,
            is_scatter_trigger=is_trigger,
            scatter_count=scatter_count
        )

    def _evaluate_line(self, symbols: List[str]) -> Tuple[str, int, float]:
        """
        Left-to-Right evaluation with Wild substitution.
        Returns: (matched_symbol, count, multiplier)
        """
        if not symbols:
            return None, 0, 0.0
            
        first_sym = symbols[0]
        # Handling wild as first symbol
        # If first is wild, we tentatively match wild, but we need to see what's next
        # Actually, standard logic: determine the 'active' symbol for the line.
        
        active_sym = first_sym
        count = 1
        
        # If first is Wild, active is Wild (generic). We refine if we hit a non-wild.
        # e.g. W - A - A -> Match A (count 3)
        # e.g. W - W - A -> Match A (count 3)
        # e.g. W - W - W -> Match W (count 3) - usually pays highest
        
        # Scan to find first non-wild
        non_wild_sym = None
        for s in symbols:
            if s != self.wild_symbol:
                non_wild_sym = s
                break
        
        target_sym = non_wild_sym if non_wild_sym else self.wild_symbol
        
        # Now count matches of target_sym (considering Wilds)
        current_count = 0
        for s in symbols:
            if s == target_sym or s == self.wild_symbol:
                current_count += 1
            else:
                break
                
        # Check paytable
        # Paytable structure: "SYM": {3: 10, 4: 50, 5: 100}
        payouts = self.paytable.get(target_sym, {})
        mult = payouts.get(current_count, 0.0)
        
        return target_sym, current_count, mult
