import logging
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self):
        # Sliding window for error rates (last 1000 requests?)
        # Or just simple counters since startup
        self.request_count = 0
        self.error_count_4xx = 0
        self.error_count_5xx = 0
        
        # Specific counters
        self.webhook_events = defaultdict(int)
        self.webhook_failures = defaultdict(int)
        self.webhook_signatures_failed = defaultdict(int)
        
        self.payout_attempts = 0
        self.payout_success = 0
        self.payout_failed = 0
        self.webhook_replay_deduped = 0
        self.webhook_signature_invalid = 0
        self.reconciliation_runs = 0
        self.reconciliation_findings = 0
        self.reconciliation_critical = 0

    def increment_request(self):
        self.request_count += 1

    def increment_error_4xx(self):
        self.error_count_4xx += 1

    def increment_error_5xx(self):
        self.error_count_5xx += 1

    def record_webhook_event(self, provider: str, status: str):
        key = f"{provider}_{status}"
        self.webhook_events[key] += 1
        if status != "success":
            self.webhook_failures[provider] += 1

    def record_webhook_replay(self):
        self.webhook_replay_deduped += 1

    def record_payout_attempt(self):
        self.payout_attempts += 1

    def record_payout_result(self, success: bool):
        if success:
            self.payout_success += 1
        else:
            self.payout_failed += 1

    def record_webhook_signature_failure(self, provider: str):
        self.webhook_signatures_failed[provider] += 1
        self.webhook_signature_invalid += 1

    def record_reconciliation_result(self, findings: int, critical: int):
        self.reconciliation_runs += 1
        self.reconciliation_findings += findings
        self.reconciliation_critical += critical
        
        if critical > 0:
            logger.error(f"[ALERT] Critical Reconciliation Findings Detected: {critical}")

    def get_metrics(self) -> Dict:
        # Calculate failure rate
        payout_failure_rate = 0.0
        if self.payout_attempts > 0:
            payout_failure_rate = self.payout_failed / self.payout_attempts

        # Threshold Evaluation
        status = "healthy"
        alerts = []
        
        if payout_failure_rate > 0.15:
            status = "critical"
            alerts.append("Payout Failure Rate > 15%")
        elif payout_failure_rate > 0.05:
            status = "warning"
            alerts.append("Payout Failure Rate > 5%")
            
        if self.reconciliation_critical > 0:
            status = "critical"
            alerts.append("Critical Reconciliation Findings")

        return {
            "status": status,
            "alerts": alerts,
            "http": {
                "total_requests": self.request_count,
                "errors_4xx": self.error_count_4xx,
                "errors_5xx": self.error_count_5xx,
                "error_rate_5xx": (self.error_count_5xx / self.request_count) if self.request_count > 0 else 0
            },
            "webhooks": {
                "events": dict(self.webhook_events),
                "failures": dict(self.webhook_failures),
                "signature_errors": dict(self.webhook_signatures_failed),
                "signature_invalid_total": self.webhook_signature_invalid,
                "replay_deduped": self.webhook_replay_deduped
            },
            "payouts": {
                "attempts": self.payout_attempts,
                "success": self.payout_success,
                "failed": self.payout_failed,
                "failure_rate": payout_failure_rate
            },
            "reconciliation": {
                "runs": self.reconciliation_runs,
                "total_findings": self.reconciliation_findings,
                "critical_findings": self.reconciliation_critical,
                "findings_by_severity": {"critical": self.reconciliation_critical, "warning": self.reconciliation_findings - self.reconciliation_critical}
            }
        }

# Singleton instance
metrics = MetricsService()
