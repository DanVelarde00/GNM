from fastapi import APIRouter, HTTPException

from api.services import otter_service

router = APIRouter()


@router.get("/status")
def otter_status():
    return {"configured": otter_service.is_configured()}


@router.post("/pull")
def pull_otter():
    if not otter_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Otter MCP not configured. Set OTTER_MCP_URL and OTTER_MCP_TOKEN in .env.",
        )
    try:
        new_files = otter_service.pull_new_transcripts()
        return {
            "ok": True,
            "pulled": len(new_files),
            "files": [f.name for f in new_files],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
