from pydantic import BaseModel


class TrackerCreate(BaseModel):
    name: str
    description: str
    folder_name: str
    extraction_prompt: str
    icon: str = "folder"
    color: str = "#6366f1"


class TrackerDefinition(TrackerCreate):
    id: str
    created_at: str
    active: bool = True


class TrackerItem(BaseModel):
    tracker_id: str
    project: str
    file_path: str
    title: str
    date: str
    content_preview: str = ""
    tags: list[str] = []
