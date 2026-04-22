from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from api.services import weekly_report_service

router = APIRouter()


class WeeklyReportRequest(BaseModel):
    target_date: str | None = None  # YYYY-MM-DD, defaults to current week


@router.post("/generate")
def generate_weekly_reports(req: WeeklyReportRequest | None = None):
    target = None
    if req and req.target_date:
        target = datetime.strptime(req.target_date, "%Y-%m-%d")
    results = weekly_report_service.generate_weekly_reports(target)
    return {"ok": True, "reports": results}
