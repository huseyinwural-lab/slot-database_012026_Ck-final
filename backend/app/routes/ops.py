from fastapi import APIRouter, Depends
from app.services.metrics import metrics
from app.routes.auth_snippet import get_current_admin
from app.models.sql_models import AdminUser

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])

@router.get("/dashboard")
async def get_ops_dashboard(current_admin: AdminUser = Depends(get_current_admin)):
    """
    Operational Dashboard for Monitoring
    """
    return metrics.get_metrics()
