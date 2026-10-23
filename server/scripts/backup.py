"""Back up the server's data to another folder (e.g. an external drive or a mounted cloud disk).

  python scripts/backup.py /path/to/backup-folder

- The database is copied with SQLite's online backup, so it is safe while the server runs.
- Stored files never change once written, so only files not already in the backup are copied.
Run it nightly (cron or a scheduled task), then copy the backup folder somewhere off the server.
"""
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path


def backup(data_dir, dest):
    data_dir, dest = Path(data_dir), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(data_dir / "anigit.db"))
    dst = sqlite3.connect(str(dest / "anigit.db.tmp"))
    src.backup(dst)
    dst.close()
    src.close()
    os.replace(dest / "anigit.db.tmp", dest / ("anigit-%s.db" % time.strftime("%Y%m%d-%H%M%S")))
    copied = 0
    objs = data_dir / "objects"
    for f in objs.rglob("*"):
        if f.is_file() and f.parent.name != "tmp":
            target = dest / "objects" / f.relative_to(objs)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
                copied += 1
    return copied


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    data = os.environ.get("ANIGIT_DATA", "./data")
    print("Backed up database and %d new files to %s" % (backup(data, sys.argv[1]), sys.argv[1]))
