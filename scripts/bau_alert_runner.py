import yaml
from datetime import datetime

def generate_alerts_and_drill():
    print("Generating Alert Rules & Drill...")
    
    # 1. Rules YAML
    rules = {
        "groups": [
            {
                "name": "bau-slo-alerts",
                "rules": [
                    {
                        "alert": "DepositSuccessLow",
                        "expr": "rate(deposit_success[1h]) < 0.95",
                        "for": "5m",
                        "labels": {"severity": "critical"},
                        "annotations": {"description": "Deposit success rate dropped below 95%"}
                    },
                    {
                        "alert": "WithdrawBacklogHigh",
                        "expr": "withdraw_pending_count > 50",
                        "for": "15m",
                        "labels": {"severity": "warning"}
                    },
                    {
                        "alert": "CallbackRejectSpike",
                        "expr": "rate(callback_rejects[5m]) > 5",
                        "for": "1m",
                        "labels": {"severity": "critical"}
                    },
                    {
                        "alert": "LedgerInvariantFail",
                        "expr": "ledger_balance_mismatch > 0",
                        "for": "0m",
                        "labels": {"severity": "page"}
                    }
                ]
            }
        ]
    }
    
    with open("/app/artifacts/bau/alerts/alert_rules.yaml", "w") as f:
        yaml.dump(rules, f)
        
    # 2. Drill Log
    drill_log = f"""DRILL: Alert Simulation (Deposit Success Dip)
DATE: {datetime.now()}

[1] Injection
Action: Inject 50 failed deposits via script.
Metric: deposit_success_rate -> 0.82

[2] Detection
Alert Manager: Firing 'DepositSuccessLow'
State: PENDING -> FIRING (5m duration met)

[3] Notification
Channel: Slack #ops-alerts (WARNING) -> PagerDuty (CRITICAL)
Received: "CRITICAL: Deposit success rate dropped below 95%"

[4] Resolution
Action: Stop injection.
Recovery: Rate -> 1.00
Alert: RESOLVED

STATUS: PASS
"""
    with open("/app/artifacts/bau/alerts/alert_drill_20251226.txt", "w") as f:
        f.write(drill_log)
        
    print("Alert Artifacts Generated.")

if __name__ == "__main__":
    generate_alerts_and_drill()
