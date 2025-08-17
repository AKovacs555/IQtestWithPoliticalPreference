from fastapi import APIRouter, Depends, HTTPException
from backend.routes.dependencies import get_current_user
from backend import db

router = APIRouter(prefix="/points", tags=["points"])

@router.post("/daily_claim")
def daily_claim(user: dict = Depends(get_current_user)):
    """Claim daily completion points (ensures one credit per day)."""
    try:
        success = db.credit_points_once_per_day(str(user["id"]), 1, "daily_complete", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to claim daily points")
    # Return whether a point was credited (False if already claimed today)
    return {"claimed": bool(success)}
