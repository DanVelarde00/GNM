from fastapi import APIRouter

from api.services import search_service

router = APIRouter()


@router.get("")
def do_search(
    q: str,
    project: str | None = None,
    type: str | None = None,
    limit: int = 20,
):
    return search_service.search(q=q, project=project, file_type=type, limit=limit)


@router.post("/rebuild")
def rebuild_index():
    count = search_service.build_full_index()
    return {"ok": True, "indexed": count}
