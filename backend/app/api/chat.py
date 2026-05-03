from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services import agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    return agent.run_chat(payload.message, payload.conversation_id)


@router.get("/conversations")
def conversations():
    return agent.list_conversations()


@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: str):
    return agent.list_messages(conversation_id)

