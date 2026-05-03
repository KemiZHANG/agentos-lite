from fastapi import APIRouter

from app.services import llmops

router = APIRouter(prefix="/llmops", tags=["llmops"])


@router.get("")
def dashboard():
    return llmops.dashboard()


@router.get("/runs/{agent_run_id}")
def run_detail(agent_run_id: str):
    return llmops.run_detail(agent_run_id)
