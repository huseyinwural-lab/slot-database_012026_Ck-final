import logging
from collections import defaultdict, deque
import time
from typing import Dict, Deque

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

    def record_webhook_signature_failure(self, provider: str):
        self.webhook_signatures_failed[provider] += 1

    def record_reconciliation_result(self, findings: int, critical: int):
        self.reconciliation_runs += 1
        self.reconciliation_findings += findings
        self.reconciliation_critical += critical
        
        if critical > 0:
            logger.error(f"[ALERT] Critical Reconciliation Findings Detected: {critical}")

    def get_metrics(self) -> Dict:
        return {
            "http": {
                "total_requests": self.request_count,
                "errors_4xx": self.error_count_4xx,
                "errors_5xx": self.error_count_5xx,
                "error_rate_5xx": (self.error_count_5xx / self.request_count) if self.request_count > 0 else 0
            },
            "webhooks": {
                "events": dict(self.webhook_events),
                "failures": dict(self.webhook_failures),
                "signature_errors": dict(self.webhook_signatures_failed)
            },
            "reconciliation": {
                "runs": self.reconciliation_runs,
                "total_findings": self.reconciliation_findings,
                "critical_findings": self.reconciliation_critical
            }
        }

# Singleton instance
metrics = MetricsService()
