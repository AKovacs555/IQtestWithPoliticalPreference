from fastapi import APIRouter, HTTPException
from supabase import create_client
import os

router = APIRouter(prefix="/exam", tags=["exam"])

@router.get("/generate")
async def generate_exam(easy: int = 9, medium: int = 12, hard: int = 9):
    supabase = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_ANON_KEY", ""),
    )
    resp = supabase.rpc(
        "fetch_exam",
        {"_easy": easy, "_med": medium, "_hard": hard},
    ).execute()
    if resp.error:
        raise HTTPException(500, resp.error.message)
    return {"items": resp.data}
