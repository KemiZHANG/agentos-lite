from fastapi import APIRouter

from app.models.schemas import CodebaseIndexRequest, FindFilesRequest, RepoQuestionRequest, TestSuggestionRequest
from app.services import codebase

router = APIRouter(prefix="/codebase", tags=["codebase"])


@router.get("/repositories")
def repositories():
    return codebase.list_repositories()


@router.post("/index")
def index_repository(payload: CodebaseIndexRequest):
    return codebase.index_repository(payload.name, payload.root_path)


@router.post("/index-current")
def index_current_repository():
    return codebase.index_current_repository()


@router.get("/repo-map")
def repo_map(repository_id: str | None = None):
    return codebase.repo_map(repository_id)


@router.get("/search")
def search(q: str, repository_id: str | None = None):
    return codebase.search_codebase(q, repository_id)


@router.post("/question")
def question(payload: RepoQuestionRequest):
    return codebase.answer_repo_question(payload.question, payload.repository_id)


@router.post("/find-files")
def find_files(payload: FindFilesRequest):
    return codebase.find_relevant_files(payload.issue, payload.repository_id)


@router.post("/test-suggestions")
def test_suggestions(payload: TestSuggestionRequest):
    return codebase.generate_test_suggestions(payload.target, payload.repository_id)
