from fastapi import APIRouter

from app.services import llmops

router = APIRouter(prefix="/llmops", tags=["llmops"])


@router.get("")
def dashboard():
    return llmops.dashboard()

