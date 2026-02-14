from fastapi import APIRouter, Response
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.metrics import metrics

router = APIRouter(prefix="/metrics", tags=["monitoring"])

# Initialize Instrumentator but don't expose route yet (we do it manually or via mount)
# Actually, the standard way is to use .instrument(app).expose(app) in server.py
# But we can also expose a custom router if we want auth.
# For now, let's keep it standard in server.py, this file is just a placeholder or for custom metrics view.

@router.get("/")
def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
