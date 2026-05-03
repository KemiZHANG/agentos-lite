from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["safe", "approval_required", "blocked"]
MemoryType = Literal["user_preference", "project_context", "tool_result", "note"]
TaskStatus = Literal["pending", "active", "paused", "completed"]


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class Citation(BaseModel):
    source: str
    title: str
    source_type: str | None = None
    document_name: str | None = None
    chunk_id: str | None = None
    file_path: str | None = None
    short_snippet: str | None = None
    relevance_score: float | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceStep(BaseModel):
    step: str
    status: str
    detail: str
    data: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    response_language: Literal["en", "zh"] = "en"


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    intent: str
    confidence: str
    citations: list[Citation] = Field(default_factory=list)
    trace: list[TraceStep] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    approval_required: bool = False


class MemoryCreate(BaseModel):
    type: MemoryType = "note"
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    type: MemoryType | None = None
    title: str | None = None
    content: str | None = None
    metadata: dict[str, Any] | None = None


class Memory(MemoryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    risk_level: RiskLevel
    enabled: bool = True


class ApprovalDecision(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer_note: str | None = None


class CodebaseIndexRequest(BaseModel):
    name: str = "sample_repo"
    root_path: str = "examples/sample_repo"


class RepoQuestionRequest(BaseModel):
    repository_id: str | None = None
    question: str


class FindFilesRequest(BaseModel):
    repository_id: str | None = None
    issue: str


class TestSuggestionRequest(BaseModel):
    repository_id: str | None = None
    target: str


class ScheduledTaskCreate(BaseModel):
    name: str
    description: str = ""
    schedule: str
    status: TaskStatus = "pending"
    payload: dict[str, Any] = Field(default_factory=dict)


class ScheduledTaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    schedule: str | None = None
    status: TaskStatus | None = None
    payload: dict[str, Any] | None = None


class PromptTemplateCreate(BaseModel):
    name: str
    version: str
    task_type: str
    content: str
    active: bool = True
