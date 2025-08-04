from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/user", tags=["user"])

class NationalityPayload(BaseModel):
    user_id: str
    nationality: str

class PartyPayload(BaseModel):
    user_id: str
    party_ids: list[int]

@router.post('/nationality')
async def set_nationality(payload: NationalityPayload):
    supabase = get_supabase_client()
    data = {'nationality': payload.nationality}
    try:
        supabase.table('users').update(data).eq('hashed_id', payload.user_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'status': 'ok'}

@router.get('/parties/{country}')
async def parties(country: str):
    supabase = get_supabase_client()
    try:
        rows = supabase.table('political_parties').select('*').eq('country', country).execute().data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'parties': rows}

@router.post('/party')
async def save_party(payload: PartyPayload):
    supabase = get_supabase_client()
    try:
        supabase.table('users').update({'party_ids': payload.party_ids}).eq('hashed_id', payload.user_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'status': 'ok'}
