from fastapi import APIRouter, Depends
from app.utils.permissions import feature_required

# Stub for Simulator with Feature Check
router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])

@router.get("/")
async def get_simulator_status(
    _ = Depends(feature_required("can_use_game_robot"))
):
    return {"status": "active"}
