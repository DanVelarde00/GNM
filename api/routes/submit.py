from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

import config

router = APIRouter()

_SOURCE_DIRS = {
    "otter": config.INBOX_OTTER,
    "inq": config.INBOX_INQ,
    "manual": config.INBOX_MANUAL,
}


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form("manual"),
):
    target_dir = _SOURCE_DIRS.get(source_type)
    if not target_dir:
        raise HTTPException(400, f"Invalid source_type: {source_type}")
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)
    return {"ok": True, "path": str(dest), "filename": file.filename}


class TextSubmission(BaseModel):
    content: str
    source_type: str = "manual"
    filename: str = "note.md"


@router.post("/text")
def submit_text(req: TextSubmission):
    target_dir = _SOURCE_DIRS.get(req.source_type)
    if not target_dir:
        raise HTTPException(400, f"Invalid source_type: {req.source_type}")
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / req.filename
    dest.write_text(req.content, encoding="utf-8")
    return {"ok": True, "path": str(dest), "filename": req.filename}
