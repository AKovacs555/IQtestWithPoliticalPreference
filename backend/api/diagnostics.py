import os
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["diagnostics"])

@router.get("/translate-model")
def translate_model():
    return {"model": os.getenv("TRANSLATION_MODEL", "gpt-5")}
