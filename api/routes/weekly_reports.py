from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from api.services import weekly_report_service

router = APIRouter()


class WeeklyReportRequest(BaseModel):
    target_date: Optional[str] = None  # YYYY-MM-DD, defaults to current week


@router.post("/generate")
def generate_weekly_reports(req: Optional[WeeklyReportRequest] = None):
    target = None
    if req and req.target_date:
        target = datetime.strptime(req.target_date, "%Y-%m-%d")
    results = weekly_report_service.generate_weekly_reports(target)
    return {"ok": True, "reports": results}
