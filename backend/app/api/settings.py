from fastapi import APIRouter

from app.core.config import get_settings
from app.db.database import POSTGRES_PGVECTOR_SCHEMA
from app.models.schemas import PromptTemplateCreate
from app.services import prompts, scheduler
from app.services.llm import provider_health_check
from app.models.schemas import ScheduledTaskCreate, ScheduledTaskUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def settings():
    config = get_settings()
    return {
        "app_name": config.app_name,
        "environment": config.environment,
        "sqlite_database": config.sqlite_path.name,
        "llm_provider": config.llm_provider,
        "active_model": config.active_model,
        "llm_api_key_configured": config.llm_api_key_configured,
        "llm_fallback_to_mock": config.llm_fallback_to_mock,
        "embedding_provider": config.embedding_provider,
        "embedding_model": config.embedding_model,
        "rag_mode": config.rag_mode,
        "strict_citation_mode": config.strict_citation_mode,
        "demo_mode": config.demo_mode,
        "max_llm_calls_per_session": config.max_llm_calls_per_session,
        "max_llm_calls_per_day": config.max_llm_calls_per_day,
        "default_user_id": config.default_user_id,
    }


@router.get("/provider-health")
def provider_health():
    return provider_health_check()


@router.get("/postgres-schema")
def postgres_schema():
    return {"schema": POSTGRES_PGVECTOR_SCHEMA}


@router.get("/prompts")
def list_prompts():
    return prompts.list_prompts()


@router.post("/prompts")
def create_prompt(payload: PromptTemplateCreate):
    import uuid
    from app.db.database import get_db, utc_now

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO prompt_templates (id, name, version, task_type, content, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                payload.name,
                payload.version,
                payload.task_type,
                payload.content,
                1 if payload.active else 0,
                utc_now(),
            ),
        )
    return {"status": "created", "name": payload.name, "version": payload.version}


@router.get("/scheduled-tasks")
def list_scheduled_tasks():
    return scheduler.list_tasks()


@router.post("/scheduled-tasks")
def create_scheduled_task(payload: ScheduledTaskCreate):
    return scheduler.create_task(payload.model_dump())


@router.put("/scheduled-tasks/{task_id}")
def update_scheduled_task(task_id: str, payload: ScheduledTaskUpdate):
    return scheduler.update_task(task_id, payload.model_dump(exclude_none=True))
