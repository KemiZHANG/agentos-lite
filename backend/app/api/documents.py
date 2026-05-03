from fastapi import APIRouter, File, UploadFile

from app.services import rag

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents():
    return rag.list_documents()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    return rag.ingest_document(file.filename or "untitled.txt", content)


@router.get("/search")
def search_documents(q: str, limit: int = 5):
    return rag.retrieve(q, limit=limit)

