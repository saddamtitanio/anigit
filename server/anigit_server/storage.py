import os
import secrets
from pathlib import Path


class ObjectStore:
    """Files named by their SHA-256. Written once, never changed."""

    def __init__(self, root):
        self.root = Path(root)
        (self.root / "tmp").mkdir(parents=True, exist_ok=True)

    def new_tmp(self) -> Path:
        return self.root / "tmp" / secrets.token_hex(8)

    def path(self, project_id: int, h: str) -> Path:
        return self.root / str(project_id) / h[:2] / h

    def install(self, tmp: Path, project_id: int, h: str):
        dest = self.path(project_id, h)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, dest)   # atomic: a half-uploaded file is never visible
