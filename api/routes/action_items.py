from fastapi import APIRouter
from pydantic import BaseModel

from api.services import vault_service

router = APIRouter()


class ToggleRequest(BaseModel):
    file_path: str
    task_index: int
    completed: bool


@router.get("")
def get_action_items(
    project: str | None = None,
    person: str | None = None,
    completed: bool | None = None,
):
    return vault_service.scan_action_items(project=project, person=person, completed=completed)


@router.put("/toggle")
def toggle_action_item(req: ToggleRequest):
    vault_service.toggle_action_item(req.file_path, req.task_index, req.completed)
    return {"ok": True}
