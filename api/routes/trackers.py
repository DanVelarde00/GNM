from fastapi import APIRouter, HTTPException

from api.models.tracker_models import TrackerCreate, TrackerDefinition, TrackerItem
from api.services import tracker_service
from api.services.process_manager import ProcessManager

router = APIRouter()


@router.get("", response_model=list[TrackerDefinition])
def list_trackers():
    return tracker_service.load_trackers()


@router.post("", response_model=TrackerDefinition)
def create_tracker(req: TrackerCreate):
    tracker = tracker_service.create_tracker(req)
    # Restart processor so it picks up new tracker prompt
    ProcessManager.instance().restart()
    return tracker


@router.get("/{tracker_id}", response_model=TrackerDefinition)
def get_tracker(tracker_id: str):
    t = tracker_service.get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, "Tracker not found")
    return t


@router.put("/{tracker_id}", response_model=TrackerDefinition)
def update_tracker(tracker_id: str, updates: dict):
    t = tracker_service.update_tracker(tracker_id, updates)
    if not t:
        raise HTTPException(404, "Tracker not found")
    ProcessManager.instance().restart()
    return t


@router.delete("/{tracker_id}")
def delete_tracker(tracker_id: str):
    ok = tracker_service.delete_tracker(tracker_id)
    if not ok:
        raise HTTPException(404, "Tracker not found")
    ProcessManager.instance().restart()
    return {"ok": True}


@router.get("/{tracker_id}/items", response_model=list[TrackerItem])
def get_tracker_items(tracker_id: str):
    return tracker_service.get_tracker_items(tracker_id)
