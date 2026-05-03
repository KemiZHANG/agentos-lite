from fastapi import APIRouter

from app.models.schemas import ApprovalDecision
from app.services import tools

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals():
    return tools.list_approvals()


@router.post("/{approval_id}/decision")
def decide(approval_id: str, payload: ApprovalDecision):
    return tools.decide_approval(approval_id, payload.status, payload.reviewer_note)

