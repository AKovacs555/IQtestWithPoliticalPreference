from fastapi import APIRouter, Depends
from backend.db import list_pricing_rules, upsert_pricing_rule, delete_pricing_rule
from backend.routes.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin-pricing"])

@router.get("/pricing_rules", dependencies=[Depends(require_admin)])
async def pricing_rules_list():
    return {"rules": list_pricing_rules()}

@router.post("/pricing_rules", dependencies=[Depends(require_admin)])
async def pricing_rules_create(payload: dict):
    rule = upsert_pricing_rule(payload)
    return {"rule": rule}

@router.put("/pricing_rules/{rule_id}", dependencies=[Depends(require_admin)])
async def pricing_rules_update(rule_id: str, payload: dict):
    payload["id"] = rule_id
    rule = upsert_pricing_rule(payload)
    return {"rule": rule}

@router.delete("/pricing_rules/{rule_id}", dependencies=[Depends(require_admin)])
async def pricing_rules_delete(rule_id: str):
    delete_pricing_rule(rule_id)
    return {"status": "ok"}
