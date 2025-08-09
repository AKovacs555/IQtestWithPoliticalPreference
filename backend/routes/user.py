from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.deps.supabase_client import get_supabase_client
from backend.deps.auth import get_current_user

router = APIRouter(prefix="/user", tags=["user"])

class NationalityPayload(BaseModel):
    user_id: str
    nationality: str

@router.post('/nationality')
async def set_nationality(payload: NationalityPayload):
    supabase = get_supabase_client()
    data = {'nationality': payload.nationality}
    try:
        supabase.table('users').update(data).eq('hashed_id', payload.user_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'status': 'ok'}


@router.get("/credits")
async def get_credits(user: dict = Depends(get_current_user)):
    return {
        "free_attempts": user.get("free_attempts"),
        "pro_active_until": user.get("pro_active_until"),
    }


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()
    rows = (
        supabase.table("quiz_attempts")
        .select("*")
        .eq("user_id", user.get("hashed_id"))
        .execute()
        .data
        or []
    )
    rows = [
        r
        for r in rows
        if r.get("status") in {"submitted", "timeout", "abandoned"}
    ]
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = rows[start:end]
    attempts = [
        {
            "date": r.get("created_at"),
            "set": r.get("set_id"),
            "score": r.get("iq_score"),
            "percentile": r.get("percentile"),
            "duration": r.get("duration"),
        }
        for r in sliced
    ]
    return {"attempts": attempts}

