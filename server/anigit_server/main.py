import hashlib
import os
import re
import sqlite3
import time
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import commits, db
from .config import Settings
from .security import (DUMMY_HASH, LoginLimiter, hash_password, new_token,
                       token_digest, verify_password)
from .storage import ObjectStore

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
HASH_RE = commits.HASH_RE
RANK = {"read": 1, "write": 2, "owner": 3}


def err(status, code, message, **extra):
    """Every error has a short code for the GUI and a plain-words message for the animator."""
    return HTTPException(status, detail={"error": code, "message": message, **extra})


class Credentials(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=200)


class NewProject(BaseModel):
    name: str


class HaveRequest(BaseModel):
    hashes: List[str] = Field(max_length=20000)


class BranchMove(BaseModel):
    old: Optional[str] = None   # the commit you think the branch is at ("" or null for a new branch)
    new: str


class MemberRole(BaseModel):
    role: str


def create_app(settings: Settings = None) -> FastAPI:
    s = settings or Settings.from_env()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    db_path = s.data_dir / "anigit.db"
    db.init(db_path)
    store = ObjectStore(s.data_dir / "objects")
    limiter = LoginLimiter(max_failures=s.max_login_failures)
    app = FastAPI(title="AniGit server")

    @app.exception_handler(StarletteHTTPException)
    async def flatten(request, exc):
        body = exc.detail if isinstance(exc.detail, dict) else {"error": "error", "message": str(exc.detail)}
        return JSONResponse(body, status_code=exc.status_code)

    # ---------- helpers ----------
    def get_db():
        conn = db.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    def current_user(authorization: Optional[str] = Header(None), conn=Depends(get_db)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise err(401, "not_signed_in", "Please sign in.")
        cutoff = time.time() - s.token_days * 86400
        row = conn.execute(
            "SELECT u.* FROM tokens t JOIN users u ON u.id=t.user_id "
            "WHERE t.token_hash=? AND t.created>?",
            (token_digest(authorization[7:].strip()), cutoff)).fetchone()
        if not row:
            raise err(401, "bad_token", "Your sign-in has expired. Please sign in again.")
        return row

    def check_name(v, what="name"):
        if not NAME_RE.match(v or ""):
            raise err(400, "bad_name", "A %s can only use letters, numbers, dot, dash and underscore (up to 64)." % what)

    def check_hash(h):
        if not HASH_RE.match(h or ""):
            raise err(400, "bad_fingerprint", "That is not a valid file fingerprint.")

    def load_project(conn, user, owner, name, need):
        check_name(owner, "username")
        check_name(name, "project name")
        p = conn.execute(
            "SELECT p.*, o.username AS owner_name FROM projects p JOIN users o ON o.id=p.owner_id "
            "WHERE o.username=? AND p.name=?", (owner, name)).fetchone()
        role = None
        if p:
            if p["owner_id"] == user["id"]:
                role = "owner"
            else:
                m = conn.execute("SELECT role FROM members WHERE project_id=? AND user_id=?",
                                 (p["id"], user["id"])).fetchone()
                role = m["role"] if m else None
        if role is None:   # same answer whether it exists or not, so names don't leak
            raise err(404, "no_such_project", "No project with that name, or you don't have access to it.")
        if RANK[role] < RANK[need]:
            raise err(403, "not_allowed", "You have %s access to this project, which is not enough for this action." % role)
        return p, role

    def log(conn, pid, uid, action, detail):
        conn.execute("INSERT INTO activity(project_id,user_id,action,detail,ts) VALUES (?,?,?,?,?)",
                     (pid, uid, action, detail, time.time()))

    def create_user(conn, username, password, admin):
        check_name(username, "username")
        try:
            conn.execute("INSERT INTO users(username,pw_hash,is_admin,created) VALUES (?,?,?,?)",
                         (username, hash_password(password), 1 if admin else 0, time.time()))
        except sqlite3.IntegrityError:
            raise err(409, "user_exists", "That username is taken.")

    # ---------- accounts ----------
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.post("/api/register", status_code=201)
    def register(body: Credentials, conn=Depends(get_db)):
        first = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        if not first and not s.allow_registration:
            raise err(403, "registration_closed", "Sign-up is closed. Ask the server admin to create your account.")
        create_user(conn, body.username, body.password, admin=first)
        return {"username": body.username, "admin": first}

    @app.post("/api/users", status_code=201)
    def admin_create_user(body: Credentials, user=Depends(current_user), conn=Depends(get_db)):
        if not user["is_admin"]:
            raise err(403, "not_admin", "Only the server admin can create accounts.")
        create_user(conn, body.username, body.password, admin=False)
        return {"username": body.username}

    @app.post("/api/login")
    def login(body: Credentials, request: Request, conn=Depends(get_db)):
        key = (request.client.host if request.client else "?", body.username.lower())
        if limiter.blocked(key):
            raise err(429, "too_many_attempts", "Too many wrong passwords. Wait 15 minutes and try again.")
        row = conn.execute("SELECT * FROM users WHERE username=?", (body.username,)).fetchone()
        ok = verify_password(body.password, row["pw_hash"] if row else DUMMY_HASH)
        if not row or not ok:
            limiter.fail(key)
            raise err(401, "bad_login", "Wrong username or password.")
        limiter.reset(key)
        token = new_token()
        conn.execute("INSERT INTO tokens(token_hash,user_id,created) VALUES (?,?,?)",
                     (token_digest(token), row["id"], time.time()))
        return {"token": token, "username": row["username"]}

    @app.post("/api/logout")
    def logout(authorization: Optional[str] = Header(None), user=Depends(current_user), conn=Depends(get_db)):
        conn.execute("DELETE FROM tokens WHERE token_hash=?", (token_digest(authorization[7:].strip()),))
        return {"ok": True}

    # ---------- projects ----------
    @app.post("/api/projects", status_code=201)
    def create_project(body: NewProject, user=Depends(current_user), conn=Depends(get_db)):
        check_name(body.name, "project name")
        try:
            cur = conn.execute("INSERT INTO projects(owner_id,name,created) VALUES (?,?,?)",
                               (user["id"], body.name, time.time()))
        except sqlite3.IntegrityError:
            raise err(409, "project_exists", "You already have a project with that name.")
        conn.execute("INSERT INTO branches(project_id,name,commit_id,updated) VALUES (?,?,?,?)",
                     (cur.lastrowid, "main", "", time.time()))
        log(conn, cur.lastrowid, user["id"], "create", "project created")
        return {"owner": user["username"], "name": body.name, "path": "%s/%s" % (user["username"], body.name)}

    @app.get("/api/projects")
    def list_projects(user=Depends(current_user), conn=Depends(get_db)):
        rows = conn.execute(
            "SELECT p.name, o.username AS owner, 'owner' AS role FROM projects p JOIN users o ON o.id=p.owner_id WHERE p.owner_id=? "
            "UNION ALL SELECT p.name, o.username, m.role FROM members m JOIN projects p ON p.id=m.project_id "
            "JOIN users o ON o.id=p.owner_id WHERE m.user_id=? ORDER BY 1", (user["id"], user["id"])).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/projects/{owner}/{name}")
    def project_info(owner: str, name: str, user=Depends(current_user), conn=Depends(get_db)):
        p, role = load_project(conn, user, owner, name, "read")
        branches = {r["name"]: r["commit_id"] for r in
                    conn.execute("SELECT name, commit_id FROM branches WHERE project_id=?", (p["id"],))}
        members = [{"username": r["username"], "role": r["role"]} for r in conn.execute(
            "SELECT u.username, m.role FROM members m JOIN users u ON u.id=m.user_id WHERE m.project_id=?", (p["id"],))]
        return {"owner": p["owner_name"], "name": p["name"], "your_role": role,
                "branches": branches, "members": members}

    @app.delete("/api/projects/{owner}/{name}")
    def delete_project(owner: str, name: str, user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "owner")
        conn.execute("DELETE FROM projects WHERE id=?", (p["id"],))
        import shutil
        shutil.rmtree(store.root / str(p["id"]), ignore_errors=True)
        return {"ok": True}

    # ---------- files ----------
    @app.post("/api/projects/{owner}/{name}/have")
    def have(owner: str, name: str, body: HaveRequest, user=Depends(current_user), conn=Depends(get_db)):
        """The GUI sends fingerprints; the server says which ones it is missing."""
        p, _ = load_project(conn, user, owner, name, "read")
        for h in body.hashes:
            check_hash(h)
        known = set()
        wanted = list(set(body.hashes))
        for i in range(0, len(wanted), 500):
            chunk = wanted[i:i + 500]
            q = "SELECT hash FROM objects WHERE project_id=? AND hash IN (%s)" % ",".join("?" * len(chunk))
            known.update(r["hash"] for r in conn.execute(q, [p["id"]] + chunk))
        return {"missing": [h for h in body.hashes if h not in known]}

    @app.put("/api/projects/{owner}/{name}/objects/{h}")
    async def put_object(owner: str, name: str, h: str, request: Request,
                         user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "write")
        check_hash(h)
        too_big = err(413, "file_too_large", "That file is larger than the server's limit of %d MB." % (s.max_object_bytes // 1048576))
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > s.max_object_bytes:
            raise too_big
        if conn.execute("SELECT 1 FROM objects WHERE project_id=? AND hash=?", (p["id"], h)).fetchone():
            async for _ in request.stream():
                pass
            return JSONResponse({"stored": False}, status_code=200)   # already had it
        tmp = store.new_tmp()
        digest, size = hashlib.sha256(), 0
        try:
            with open(tmp, "wb") as f:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > s.max_object_bytes:
                        raise too_big
                    digest.update(chunk)
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
            if digest.hexdigest() != h:
                raise err(400, "fingerprint_mismatch", "The uploaded file doesn't match its fingerprint, so it was damaged in transit. Try again.")
            used = conn.execute("SELECT COALESCE(SUM(size),0) FROM objects WHERE project_id=?", (p["id"],)).fetchone()[0]
            if used + size > s.project_quota_bytes:
                raise err(413, "quota_exceeded", "This project has reached its storage limit of %d GB." % (s.project_quota_bytes // 1024 ** 3))
            store.install(tmp, p["id"], h)
            conn.execute("INSERT OR IGNORE INTO objects(project_id,hash,size) VALUES (?,?,?)", (p["id"], h, size))
        finally:
            tmp.unlink(missing_ok=True)
        return JSONResponse({"stored": True}, status_code=201)

    @app.get("/api/projects/{owner}/{name}/objects/{h}")
    def get_object(owner: str, name: str, h: str, user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "read")
        check_hash(h)
        if not conn.execute("SELECT 1 FROM objects WHERE project_id=? AND hash=?", (p["id"], h)).fetchone():
            raise err(404, "no_such_file", "The server doesn't have that file.")
        return FileResponse(store.path(p["id"], h), media_type="application/octet-stream")

    # ---------- branches ----------
    @app.put("/api/projects/{owner}/{name}/branches/{branch}")
    def move_branch(owner: str, name: str, branch: str, body: BranchMove,
                    user=Depends(current_user), conn=Depends(get_db)):
        """Move a branch to `new`, but ONLY if it is still at `old`. This one rule stops lost work."""
        p, _ = load_project(conn, user, owner, name, "write")
        check_name(branch, "branch name")
        check_hash(body.new)
        expected = body.old or ""
        if expected:
            check_hash(expected)

        # 1. the new commit and everything it needs must already be uploaded
        if not conn.execute("SELECT 1 FROM objects WHERE project_id=? AND hash=?", (p["id"], body.new)).fetchone():
            raise err(400, "commit_not_uploaded", "Upload the commit record before moving the branch.")
        try:
            commit = commits.parse_commit(store.path(p["id"], body.new).read_bytes())
        except (ValueError, OSError) as e:
            raise err(400, "bad_commit", str(e))
        refs = commits.referenced(commit)
        have_rows = set(r["hash"] for r in conn.execute(
            "SELECT hash FROM objects WHERE project_id=? AND hash IN (%s)" % ",".join("?" * len(refs)),
            [p["id"]] + refs)) if refs else set()
        missing = [h for h in refs if h not in have_rows]
        if missing:
            raise err(400, "missing_files", "The commit refers to %d file(s) that were not uploaded." % len(missing), missing=missing)

        # 2. compare-and-move, atomically
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur = conn.execute("SELECT commit_id FROM branches WHERE project_id=? AND name=?", (p["id"], branch)).fetchone()
            actual = cur["commit_id"] if cur else ""
            if actual != expected:
                conn.execute("ROLLBACK")
                raise err(409, "branch_moved",
                          "Someone else has pushed to '%s' since you last pulled. Pull their changes first, then push again." % branch,
                          current=actual)
            if actual and actual != body.new and not commits.is_ancestor(store, p["id"], actual, body.new):
                conn.execute("ROLLBACK")
                raise err(409, "not_fast_forward",
                          "This would remove commits already on '%s'. Pull and merge first." % branch, current=actual)
            conn.execute("INSERT INTO branches(project_id,name,commit_id,updated) VALUES (?,?,?,?) "
                         "ON CONFLICT(project_id,name) DO UPDATE SET commit_id=excluded.commit_id, updated=excluded.updated",
                         (p["id"], branch, body.new, time.time()))
            log(conn, p["id"], user["id"], "push", "%s: %s -> %s" % (branch, (actual or "new")[:8], body.new[:8]))
            conn.execute("COMMIT")
        except HTTPException:
            raise
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return {"branch": branch, "commit": body.new}

    @app.delete("/api/projects/{owner}/{name}/branches/{branch}")
    def delete_branch(owner: str, name: str, branch: str, user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "write")
        if branch == "main":
            raise err(400, "cannot_delete_main", "The main branch can't be deleted.")
        n = conn.execute("DELETE FROM branches WHERE project_id=? AND name=?", (p["id"], branch)).rowcount
        if not n:
            raise err(404, "no_such_branch", "There is no branch with that name.")
        log(conn, p["id"], user["id"], "delete_branch", branch)
        return {"ok": True}

    # ---------- members and activity ----------
    @app.put("/api/projects/{owner}/{name}/members/{username}")
    def set_member(owner: str, name: str, username: str, body: MemberRole,
                   user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "owner")
        if body.role not in ("read", "write"):
            raise err(400, "bad_role", "Role must be 'read' or 'write'.")
        target = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if not target:
            raise err(404, "no_such_user", "There is no account with that username.")
        if target["id"] == p["owner_id"]:
            raise err(400, "is_owner", "The owner already has full access.")
        conn.execute("INSERT INTO members(project_id,user_id,role) VALUES (?,?,?) "
                     "ON CONFLICT(project_id,user_id) DO UPDATE SET role=excluded.role", (p["id"], target["id"], body.role))
        log(conn, p["id"], user["id"], "member", "%s -> %s" % (username, body.role))
        return {"username": username, "role": body.role}

    @app.delete("/api/projects/{owner}/{name}/members/{username}")
    def remove_member(owner: str, name: str, username: str, user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "owner")
        conn.execute("DELETE FROM members WHERE project_id=? AND user_id=(SELECT id FROM users WHERE username=?)",
                     (p["id"], username))
        log(conn, p["id"], user["id"], "member", "%s removed" % username)
        return {"ok": True}

    @app.get("/api/projects/{owner}/{name}/activity")
    def activity(owner: str, name: str, limit: int = 100, user=Depends(current_user), conn=Depends(get_db)):
        p, _ = load_project(conn, user, owner, name, "read")
        rows = conn.execute(
            "SELECT a.ts, u.username, a.action, a.detail FROM activity a JOIN users u ON u.id=a.user_id "
            "WHERE a.project_id=? ORDER BY a.id DESC LIMIT ?", (p["id"], min(max(limit, 1), 500))).fetchall()
        return [dict(r) for r in rows]

    return app
