from app.services.metrics import MetricsService

def test_ops_metrics_defaults():
    m = MetricsService()
    data = m.get_metrics()
    assert data["status"] == "healthy"
    assert data["payouts"]["failure_rate"] == 0.0
    assert len(data["alerts"]) == 0

def test_ops_metrics_payout_thresholds():
    m = MetricsService()
    
    # 1. Healthy (0/10)
    for _ in range(10):
        m.record_payout_attempt()
        m.record_payout_result(True)
    
    data = m.get_metrics()
    assert data["status"] == "healthy"
    assert data["payouts"]["failure_rate"] == 0.0
    
    # 2. Warning (1/11 = 9%)
    m.record_payout_attempt()
    m.record_payout_result(False)
    
    data = m.get_metrics()
    assert data["status"] == "warning"
    assert "Payout Failure Rate > 5%" in data["alerts"]
    
    # 3. Critical (20/100 -> 20%)
    m = MetricsService() # Reset
    for _ in range(80):
        m.record_payout_attempt()
        m.record_payout_result(True)
    for _ in range(20):
        m.record_payout_attempt()
        m.record_payout_result(False)
        
    data = m.get_metrics()
    assert data["status"] == "critical"
    assert "Payout Failure Rate > 15%" in data["alerts"]

def test_ops_metrics_reconciliation_thresholds():
    m = MetricsService()
    
    m.record_reconciliation_result(findings=5, critical=0)
    data = m.get_metrics()
    assert data["status"] == "healthy" # Findings are warning level if critical=0 (implicit)
    
    m.record_reconciliation_result(findings=1, critical=1)
    data = m.get_metrics()
    assert data["status"] == "critical"
    assert "Critical Reconciliation Findings" in data["alerts"]

def test_webhook_metrics():
    m = MetricsService()
    m.record_webhook_event("stripe", "success")
    m.record_webhook_event("adyen", "failed")
    m.record_webhook_signature_failure("stripe")
    m.record_webhook_replay()
    
    data = m.get_metrics()
    assert data["webhooks"]["events"]["stripe_success"] == 1
    assert data["webhooks"]["failures"]["adyen"] == 1
    assert data["webhooks"]["signature_errors"]["stripe"] == 1
    assert data["webhooks"]["signature_invalid_total"] == 1
    assert data["webhooks"]["replay_deduped"] == 1
