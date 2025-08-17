from fastapi import APIRouter

from backend.deps.supabase_client import get_supabase_client

router = APIRouter(tags=["leaderboard"])

VALID_STATUSES = {"submitted", "timeout", "abandoned"}

@router.get("/leaderboard")
async def get_leaderboard(limit: int = 100):
    supabase = get_supabase_client()
    attempts = (
        supabase.table("quiz_attempts").select("*").execute().data or []
    )
    best: dict[str, dict[str, float]] = {}
    for row in attempts:
        if row.get("status") not in VALID_STATUSES:
            continue
        uid = row.get("user_id")
        iq = row.get("iq_score")
        pct = row.get("percentile") or 0
        entry = best.setdefault(uid, {"best_iq": float("-inf"), "best_percentile": 0})
        if iq is not None and iq > entry["best_iq"]:
            entry["best_iq"] = iq
        if pct > entry["best_percentile"]:
            entry["best_percentile"] = pct
    users = supabase.table("app_users").select("hashed_id,display_name").execute().data or []
    name_map = {u.get("hashed_id"): u.get("display_name") for u in users}
    rows = []
    for uid, vals in best.items():
        name = name_map.get(uid) or f"Guest-{uid[:4]}"
        rows.append({
            "user_id": uid,
            "display_name": name,
            "best_iq": vals["best_iq"],
            "best_percentile": vals["best_percentile"],
        })
    rows.sort(key=lambda r: r["best_iq"], reverse=True)
    return {"leaderboard": rows[:limit]}
