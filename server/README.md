# AniGit server

Shared remote for AniGit. It stores files, keeps the branch list, and checks that a branch
hasn't moved before updating it. It never opens `.kra` files and never merges.

## Stack

| Part | Choice |
|---|---|
| App | Python + FastAPI |
| Database | SQLite (accounts, projects, members, branches, activity) |
| Files | Folder on disk, named by SHA-256 (`data/objects/<project>/<ab>/<hash>`) |
| Passwords | scrypt (standard library) |
| HTTPS | Caddy (automatic certificates) |
| Packaging | Docker Compose |

## Run it on your computer (development)

```bash
cd server
pip install -r requirements-dev.txt
pytest
uvicorn anigit_server.main:create_app --factory --reload   # http://localhost:8000/docs
```

`http://localhost:8000/docs` shows every request and lets you try them.

## Deploy to a server

1. Rent a small Linux server, install Docker, point a domain name at it.
2. `cp .env.example .env` and set `DOMAIN`.
3. `docker compose up -d`
4. Create the first account (it becomes the admin):
   `curl -X POST https://YOUR.DOMAIN/api/register -H 'content-type: application/json' -d '{"username":"you","password":"a-long-password"}'`
5. Create teammates' accounts as admin with `POST /api/users`, or set `ANIGIT_ALLOW_REGISTRATION=true` temporarily.

## Requests

| Request | What it does | Needs |
|---|---|---|
| `POST /api/register` | Create an account (first one = admin; later ones only if registration is open) | none |
| `POST /api/users` | Admin creates an account | admin |
| `POST /api/login`, `/api/logout` | Get or drop a sign-in token | none / signed in |
| `POST /api/projects`, `GET /api/projects` | Create / list your projects | signed in |
| `GET /api/projects/{owner}/{name}` | Branches, members, your role (used by clone and pull) | read |
| `POST .../have` | Send fingerprints, get back the ones the server is missing | read |
| `PUT .../objects/{hash}` | Upload a file. Rejected if its content doesn't match the fingerprint | write |
| `GET .../objects/{hash}` | Download a file | read |
| `PUT .../branches/{branch}` | Move a branch from `old` to `new`. Refused if it has moved or would drop commits | write |
| `DELETE .../branches/{branch}` | Delete a branch (not `main`) | write |
| `PUT/DELETE .../members/{username}` | Give someone `read` or `write` access, or remove them | owner |
| `GET .../activity` | Who pushed what and when | read |
| `DELETE /api/projects/{owner}/{name}` | Delete a project and its files | owner |

Errors look like `{"error": "branch_moved", "message": "Someone else has pushed ..."}`: a short
code for the GUI and a plain sentence to show the animator.

## Commit record format

A commit is a small JSON file uploaded like any other file:

```json
{"parents": ["<commit hash>"],
 "files": {"hero/layers/layer2": "<hash>", "maindoc.xml": "<hash>", "preview.png": "<hash>"},
 "layers": {"{layer-uuid}": "<hash>"},
 "preview": "<hash or null>", "author": "aya", "note": "Hair recolour", "timestamp": 1760000000}
```

Two parents means a merge. Before moving a branch the server checks that the commit record and every file it
lists in `parents`, `files` and `preview` have been uploaded, so a branch never points at something incomplete.

## Backups

```bash
python scripts/backup.py /path/to/backup-folder    # run nightly; copy the folder off the server
```

Test a restore at least once: copy a backup into an empty data folder and start the server on it.

## Limits (change in `.env`)

`ANIGIT_MAX_OBJECT_MB` (biggest single file), `ANIGIT_PROJECT_QUOTA_GB` (storage per project).

## Not done yet

Email or alert when the disk is nearly full, resumable uploads for very large files (a failed upload is
currently retried from the start), object storage (S3 or R2) instead of local disk, deleting files no
branch can reach, and the optional web page.
