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


@router.get("/{document_id}/chunks")
def document_chunks(document_id: str):
    return rag.list_document_chunks(document_id)


@router.post("/{document_id}/reindex")
def reindex_document(document_id: str):
    return rag.reindex_document(document_id)


@router.delete("/{document_id}")
def delete_document(document_id: str):
    rag.delete_document(document_id)
    return {"status": "deleted", "id": document_id}


@router.post("/sample-docs/load")
def load_sample_documents():
    return rag.load_sample_documents()


@router.get("/search")
def search_documents(q: str, limit: int = 5):
    return rag.retrieve(q, limit=limit)
