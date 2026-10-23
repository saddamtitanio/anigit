import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    data_dir: Path = Path("./data")
    max_object_bytes: int = 512 * 1024 * 1024        # biggest single file accepted
    project_quota_bytes: int = 50 * 1024 ** 3        # total stored per project
    allow_registration: bool = False                 # first account is always allowed
    token_days: int = 30                             # sign-in lasts this long
    max_login_failures: int = 10                     # per 15 minutes, per address + username

    @classmethod
    def from_env(cls):
        e = os.environ.get
        return cls(
            data_dir=Path(e("ANIGIT_DATA", "./data")).resolve(),
            max_object_bytes=int(e("ANIGIT_MAX_OBJECT_MB", "512")) * 1024 * 1024,
            project_quota_bytes=int(e("ANIGIT_PROJECT_QUOTA_GB", "50")) * 1024 ** 3,
            allow_registration=e("ANIGIT_ALLOW_REGISTRATION", "false").lower() == "true",
        )
