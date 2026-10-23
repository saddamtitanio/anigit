# Server features

The server stores what teammates share. It never edits layers and never decides anything for the animator. Merging happens in the GUI.

| ID | Feature | What it does | Priority | Name |
|---|---|---|---|---|
| S1 | Accounts and sign-in | Create accounts, log in, and issue tokens the GUI keeps. Passwords stored hashed | P0 |  |
| S2 | Projects | Create, list, and delete projects. Each has an owner | P0 |  |
| S3 | Object storage | Store layer files and commit records by their fingerprint, so the same file is never stored twice | P0 |  |
| S4 | Branch pointers | Keep each branch's latest commit. Reject a push if it would overwrite someone else's work (the animator must pull first) | P0 |  |
| S5 | Upload and download | Let the GUI ask "which of these do you already have?", then send only what's missing. Resume interrupted transfers | P1 |  |
| S6 | Permissions | Per project: owner, can push, read only. Check on every request | P1 |  |
| S7 | Activity log | Record who pushed what and when, for the team activity view | P2 |  |
| S8 | Layer notes | Store and return "I'm working on Hair" labels | P2 |  |
| S9 | Security | HTTPS only, rate limiting on login, limit on upload size | P0 |  |
| S10 | Backups and storage limits | Regular backups of the stored data, and a per-project storage limit with a clear error when it's reached | P1 |  |
| S11 | Deployment and monitoring | Run on a host, restart on failure, and log errors | P1 |  |
| S12 | Web page (optional) | Browse a project's history and previews in a browser without the GUI | P3 |  |

## Status in `server/`

Built and tested (13 tests): S1 accounts and sign-in, S2 projects, S3 file storage, S4 branch pointers with the "has it moved?" check, S5 the have/upload/download requests (not resumable yet), S6 permissions, S7 activity, S9 HTTPS config, login limit and size limits, S10 backup script and storage limit, S11 Docker setup.
Not built: S8 layer notes, S12 web page, disk-space alerts, resumable uploads.

## Decisions made

Python + FastAPI, SQLite, files on disk, Caddy for HTTPS, Docker Compose. See `server/README.md`.

## Decisions to make

- **Language and framework** (e.g. Python with FastAPI, or Node). Pick whatever the team already knows.
- **Where objects are stored:** server disk first; move to object storage (S3-style) if it grows.
- **Database** for accounts, projects, and branch pointers: SQLite to start, PostgreSQL later.
- **How big is a team?** Under about 10 people keeps S4 and S6 simple.
