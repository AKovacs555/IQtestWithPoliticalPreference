from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.deps.auth import get_current_user
from backend.db import credit_points, get_points

router = APIRouter(prefix="/ads", tags=["ads"])

class AdStartPayload(BaseModel):
    pass

@router.post("/start")
async def ads_start(user: dict = Depends(get_current_user)):
    return {"status": "started"}

@router.post("/complete")
async def ads_complete(user: dict = Depends(get_current_user)):
    credit_points(str(user["id"]), 1, "ad_reward", {})
    return {"points": get_points(str(user["id"]))}
