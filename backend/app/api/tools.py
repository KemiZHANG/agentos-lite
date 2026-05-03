from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import tools

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolCallRequest(BaseModel):
    name: str
    payload: dict = Field(default_factory=dict)


@router.get("")
def list_tools():
    return tools.list_tools()


@router.get("/calls")
def list_tool_calls():
    return tools.list_tool_calls()


@router.post("/call")
def call_tool(payload: ToolCallRequest):
    return tools.call_tool(payload.name, payload.payload)

