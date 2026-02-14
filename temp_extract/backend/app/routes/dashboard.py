from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/comprehensive-stats")
async def get_dashboard_stats():
    # 1. Financial Trend (Last 30 days)
    today = datetime.utcnow()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    financial_trend = []
    for date in dates:
        deposit = random.randint(50000, 150000)
        withdrawal = random.randint(20000, 80000)
        financial_trend.append({
            "date": date,
            "deposits": deposit,
            "withdrawals": withdrawal,
            "net_cashflow": deposit - withdrawal
        })

    # 2. Retention & Churn
    retention_metrics = {
        "retention_1d": 42.5,
        "retention_7d": 18.2,
        "churn_rate": 5.4,
        "returning_players": 12450
    }

    # 3. FTD Metrics
    ftd_metrics = {
        "ftd_today": 145,
        "ftd_month": 3200,
        "conversion_rate": 28.5
    }

    # 4. Critical Alerts
    critical_alerts = [
        {"id": 1, "type": "provider_failure", "message": "Evolution Gaming API latency high", "severity": "high", "timestamp": (today - timedelta(minutes=5)).isoformat()},
        {"id": 2, "type": "payment_gateway", "message": "Stripe failure rate > 5%", "severity": "critical", "timestamp": (today - timedelta(minutes=15)).isoformat()},
        {"id": 3, "type": "fraud_engine", "message": "Risk engine queue backing up", "severity": "medium", "timestamp": (today - timedelta(minutes=45)).isoformat()},
        {"id": 4, "type": "cache_overload", "message": "Redis memory usage at 85%", "severity": "medium", "timestamp": (today - timedelta(hours=1)).isoformat()},
    ]

    # 5. Financial Summary
    financial_summary = {
        "cash_in_system": 15420000.00,
        "bonus_liabilities": 250000.00,
        "jackpot_pools": 1200000.00,
        "pending_withdrawals": 45000.00
    }

    # 6. Loss Leaders (Top Negative Performing Games)
    negative_performing_games = [
        {"game": "Mega Moolah", "provider": "Microgaming", "ggr_impact": -150000, "rtp_anomaly": 105.2},
        {"game": "Crazy Time", "provider": "Evolution", "ggr_impact": -85000, "rtp_anomaly": 99.8},
        {"game": "Book of Dead", "provider": "Games Global", "ggr_impact": -42000, "rtp_anomaly": 98.5},
        {"game": "Sweet Bonanza", "provider": "Pragmatic Play", "ggr_impact": -20000, "rtp_anomaly": 97.1},
        {"game": "Starburst", "provider": "NetEnt", "ggr_impact": -15000, "rtp_anomaly": 96.8},
    ]

    # 7. Live Bets Ticker (Mock)
    games = ["Roulette Live", "Blackjack VIP", "Gates of Olympus", "Aviator", "Lightning Dice"]
    players = ["user_882", "vip_king", "poker_face", "lucky_guy", "high_roller"]
    
    live_bets = []
    for _ in range(15): # More items for ticker
        bet = random.randint(10, 500)
        win = bet * random.choice([0, 0, 0, 1.5, 2, 5, 10])
        live_bets.append({
            "player_id": random.choice(players),
            "game": random.choice(games),
            "bet": bet,
            "win": win,
            "multiplier": round(win/bet, 2) if bet > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        })

    # 8. Bonus Performance Extended
    bonus_performance = {
        "given_count": 145,
        "redeemed_count": 112,
        "total_value": 50000.00,
        "expired_count": 12,
        "roi": 12.5, # Return on Investment %
        "wagering_completion_rate": 45.2 # %
    }
    
    # 9. Provider & Payment Health (Extended)
    provider_health = [
        {"name": "Pragmatic Play", "status": "UP", "latency": "45ms", "last_error": "None"},
        {"name": "Evolution", "status": "WARNING", "latency": "120ms", "last_error": "Timeout"},
        {"name": "NetEnt", "status": "UP", "latency": "35ms", "last_error": "None"},
    ]
    
    payment_health = [
        {"name": "Stripe", "status": "DOWN", "latency": "-", "last_error": "Gateway Timeout"},
        {"name": "Crypto", "status": "UP", "latency": "200ms", "last_error": "None"},
        {"name": "Papara", "status": "UP", "latency": "50ms", "last_error": "None"},
    ]

    return {
        "financial_trend": financial_trend,
        "retention_metrics": retention_metrics,
        "ftd_metrics": ftd_metrics,
        "critical_alerts": critical_alerts,
        "financial_summary": financial_summary,
        "negative_performing_games": negative_performing_games,
        "live_bets": live_bets,
        "bonus_performance": bonus_performance,
        "provider_health": provider_health,
        "payment_health": payment_health,
        "online_users": 124,
        "active_sessions": 90
    }
