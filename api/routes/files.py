from fastapi import APIRouter, HTTPException

from api.models.file_models import FileNode, VaultFile, FileSaveRequest, ProjectInfo
from api.services import vault_service

router = APIRouter()


@router.get("/tree", response_model=list[FileNode])
def get_tree():
    return vault_service.get_tree()


@router.get("/file", response_model=VaultFile)
def get_file(path: str):
    try:
        return vault_service.get_file(path)
    except FileNotFoundError:
        raise HTTPException(404, f"File not found: {path}")


@router.put("/file")
def save_file(req: FileSaveRequest):
    vault_service.save_file(req.path, req.content)
    return {"ok": True}


@router.get("/projects", response_model=list[ProjectInfo])
def list_projects():
    return vault_service.list_projects()
