from fastapi import APIRouter, Request, Response

from app.models.schemas import ChatRequest, ChatResponse
from app.services import agent, demo_limits

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, response: Response):
    demo_session_id = demo_limits.resolve_demo_session(request, response)
    return agent.run_chat(payload.message, payload.conversation_id, payload.response_language, demo_session_id)


@router.get("/conversations")
def conversations():
    return agent.list_conversations()


@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: str):
    return agent.list_messages(conversation_id)
