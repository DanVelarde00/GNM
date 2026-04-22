from pydantic import BaseModel


class FileNode(BaseModel):
    name: str
    path: str  # vault-relative path
    is_dir: bool = False
    children: list["FileNode"] = []


class VaultFile(BaseModel):
    path: str
    frontmatter: dict = {}
    body: str = ""
    raw: str = ""


class FileSaveRequest(BaseModel):
    path: str
    content: str


class ProjectInfo(BaseModel):
    name: str
    path: str
    has_notes: bool = False
    has_transcripts: bool = False
    has_analyzed: bool = False
    has_action_items: bool = False
    people_count: int = 0
