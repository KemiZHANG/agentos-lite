from fastapi import APIRouter

from app.models.schemas import MemoryCreate, MemoryUpdate
from app.services import memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("")
def list_memories(q: str | None = None):
    return memory.list_memories(q)


@router.post("")
def create_memory(payload: MemoryCreate):
    return memory.create_memory(payload.model_dump())


@router.put("/{memory_id}")
def update_memory(memory_id: str, payload: MemoryUpdate):
    return memory.update_memory(memory_id, payload.model_dump(exclude_none=True))


@router.delete("/{memory_id}")
def delete_memory(memory_id: str):
    memory.delete_memory(memory_id)
    return {"status": "deleted", "id": memory_id}

