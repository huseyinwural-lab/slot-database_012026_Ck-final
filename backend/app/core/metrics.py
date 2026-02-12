from prometheus_client import Counter, Histogram

class Metrics:
    def __init__(self):
        # Game Metrics
        self.bets_total = Counter(
            "game_bets_total", 
            "Total number of bets placed", 
            ["provider", "currency", "status"]
        )
        self.wins_total = Counter(
            "game_wins_total", 
            "Total number of wins processed", 
            ["provider", "currency"]
        )
        self.rollbacks_total = Counter(
            "game_rollbacks_total", 
            "Total number of rollbacks", 
            ["provider", "currency"]
        )
        
        # Financial Metrics
        self.bet_amount = Counter(
            "game_bet_amount_total",
            "Total value of bets (accumulated)",
            ["provider", "currency"]
        )
        self.win_amount = Counter(
            "game_win_amount_total",
            "Total value of wins (accumulated)",
            ["provider", "currency"]
        )
        
        # Latency
        self.engine_latency = Histogram(
            "game_engine_latency_seconds",
            "Latency of game engine operations",
            ["operation", "provider"]
        )
        
        # Wallet
        self.wallet_tx_total = Counter(
            "wallet_transactions_total",
            "Total wallet transactions",
            ["type", "status"]
        )
        # Risk
        self.risk_score_updates = Counter("risk_score_updates_total", "Total risk score updates")
        self.risk_blocks = Counter("risk_blocks_total", "Total blocked actions due to risk")
        self.risk_flags = Counter("risk_flags_total", "Total actions flagged for review")

# Global Instance
metrics = Metrics()
