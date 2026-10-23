import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from anigit_server.config import Settings
from anigit_server.main import create_app


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def commit_bytes(parents, layers, note=""):
    return json.dumps({"parents": parents, "files": layers, "preview": None, "note": note}, sort_keys=True).encode()


@pytest.fixture
def make_client(tmp_path):
    def _make(**kw):
        return TestClient(create_app(Settings(data_dir=tmp_path / "data", **kw)))
    return _make


@pytest.fixture
def c(make_client):
    return make_client()


def signup(c, name, pw="password123", first=False):
    if first:
        assert c.post("/api/register", json={"username": name, "password": pw}).status_code == 201
    tok = c.post("/api/login", json={"username": name, "password": pw}).json()["token"]
    return {"Authorization": "Bearer " + tok}


def upload(c, h, project, data):
    return c.put("/api/projects/%s/objects/%s" % (project, sha(data)), content=data, headers=h)


def push(c, h, project, branch, old, layers, parents, note=""):
    """Upload layer files + commit, then move the branch. Returns (response, commit_hash)."""
    refs = {}
    for lname, data in layers.items():
        assert upload(c, h, project, data).status_code in (200, 201)
        refs[lname] = sha(data)
    cb = commit_bytes(parents, refs, note)
    assert upload(c, h, project, cb).status_code in (200, 201)
    r = c.put("/api/projects/%s/branches/%s" % (project, branch), json={"old": old, "new": sha(cb)}, headers=h)
    return r, sha(cb)


def test_first_user_is_admin_and_registration_closes(c):
    signup(c, "aya", first=True)
    r = c.post("/api/register", json={"username": "ben", "password": "password123"})
    assert r.status_code == 403 and r.json()["error"] == "registration_closed"


def test_wrong_password_and_rate_limit(make_client):
    c = make_client(max_login_failures=3)
    signup(c, "aya", first=True)
    for _ in range(3):
        assert c.post("/api/login", json={"username": "aya", "password": "wrong-password"}).status_code == 401
    r = c.post("/api/login", json={"username": "aya", "password": "password123"})
    assert r.status_code == 429


def test_have_upload_download_roundtrip(c):
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    data = b"layer pixels"
    hh = sha(data)
    assert c.post("/api/projects/aya/hero/have", json={"hashes": [hh]}, headers=h).json()["missing"] == [hh]
    assert upload(c, h, "aya/hero", data).status_code == 201
    assert upload(c, h, "aya/hero", data).json()["stored"] is False       # second time: nothing stored
    assert c.post("/api/projects/aya/hero/have", json={"hashes": [hh]}, headers=h).json()["missing"] == []
    assert c.get("/api/projects/aya/hero/objects/" + hh, headers=h).content == data


def test_damaged_upload_is_rejected(c):
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    r = c.put("/api/projects/aya/hero/objects/" + sha(b"expected"), content=b"something else", headers=h)
    assert r.status_code == 400 and r.json()["error"] == "fingerprint_mismatch"


def test_size_limit(make_client):
    c = make_client(max_object_bytes=100)
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    assert upload(c, h, "aya/hero", b"x" * 101).status_code == 413


def test_quota(make_client):
    c = make_client(project_quota_bytes=150)
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    assert upload(c, h, "aya/hero", b"a" * 100).status_code == 201
    r = upload(c, h, "aya/hero", b"b" * 100)
    assert r.status_code == 413 and r.json()["error"] == "quota_exceeded"


def test_push_flow_and_branch_rejection(c):
    aya = signup(c, "aya", first=True)
    c.post("/api/users", json={"username": "ben", "password": "password123"}, headers=aya)
    ben = signup(c, "ben")
    c.post("/api/projects", json={"name": "hero"}, headers=aya)
    c.put("/api/projects/aya/hero/members/ben", json={"role": "write"}, headers=aya)
    P = "aya/hero"

    r, v1 = push(c, aya, P, "main", "", {"Hair": b"hair-v1", "Bg": b"bg-v1"}, [])
    assert r.status_code == 200
    assert c.get("/api/projects/aya/hero", headers=ben).json()["branches"]["main"] == v1

    # Aya moves main forward
    r, v2 = push(c, aya, P, "main", v1, {"Hair": b"hair-v2", "Bg": b"bg-v1"}, [v1])
    assert r.status_code == 200

    # Ben still thinks main is at v1: rejected, nothing overwritten
    r, v3 = push(c, ben, P, "main", v1, {"Hair": b"hair-v1", "Bg": b"bg-v2"}, [v1])
    assert r.status_code == 409 and r.json()["error"] == "branch_moved" and r.json()["current"] == v2
    assert c.get("/api/projects/aya/hero", headers=ben).json()["branches"]["main"] == v2

    # Ben pulls, merges (two parents), pushes again: accepted
    r, v4 = push(c, ben, P, "main", v2, {"Hair": b"hair-v2", "Bg": b"bg-v2"}, [v2, v3])
    assert r.status_code == 200

    # A new branch can start from an older commit
    r = c.put("/api/projects/aya/hero/branches/aya-hair", json={"old": "", "new": v1}, headers=aya)
    assert r.status_code == 200


def test_rewriting_history_is_refused(c):
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    P = "aya/hero"
    _, v1 = push(c, h, P, "main", "", {"A": b"1"}, [])
    _, v2 = push(c, h, P, "main", v1, {"A": b"2"}, [v1])
    _, other = push(c, h, P, "side", "", {"A": b"x"}, [])        # unrelated root commit
    r = c.put("/api/projects/aya/hero/branches/main", json={"old": v2, "new": other}, headers=h)
    assert r.status_code == 409 and r.json()["error"] == "not_fast_forward"


def test_commit_with_missing_files_is_refused(c):
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    cb = commit_bytes([], {"Hair": sha(b"never uploaded")})
    upload(c, h, "aya/hero", cb)
    r = c.put("/api/projects/aya/hero/branches/main", json={"old": "", "new": sha(cb)}, headers=h)
    assert r.status_code == 400 and r.json()["error"] == "missing_files"
    assert c.get("/api/projects/aya/hero", headers=h).json()["branches"]["main"] == ""   # branch untouched


def test_permissions(c):
    aya = signup(c, "aya", first=True)
    c.post("/api/users", json={"username": "ben", "password": "password123"}, headers=aya)
    c.post("/api/users", json={"username": "cy", "password": "password123"}, headers=aya)
    ben, cy = signup(c, "ben"), signup(c, "cy")
    c.post("/api/projects", json={"name": "hero"}, headers=aya)
    c.put("/api/projects/aya/hero/members/ben", json={"role": "read"}, headers=aya)

    assert c.get("/api/projects/aya/hero", headers=ben).status_code == 200
    assert upload(c, ben, "aya/hero", b"nope").status_code == 403                     # read-only
    assert c.get("/api/projects/aya/hero", headers=cy).status_code == 404              # not a member
    assert c.put("/api/projects/aya/hero/members/cy", json={"role": "write"}, headers=ben).status_code == 403
    assert [p["name"] for p in c.get("/api/projects", headers=ben).json()] == ["hero"]
    assert c.get("/api/projects", headers=cy).json() == []


def test_activity_log(c):
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    push(c, h, "aya/hero", "main", "", {"A": b"1"}, [], "first")
    acts = c.get("/api/projects/aya/hero/activity", headers=h).json()
    assert acts[0]["action"] == "push" and acts[0]["username"] == "aya"


def test_not_signed_in(c):
    assert c.get("/api/projects").status_code == 401


def test_simultaneous_pushes_only_one_wins(c):
    from concurrent.futures import ThreadPoolExecutor
    h = signup(c, "aya", first=True)
    c.post("/api/projects", json={"name": "hero"}, headers=h)
    P = "aya/hero"
    _, v1 = push(c, h, P, "main", "", {"A": b"1"}, [])
    # prepare 6 different commits that all build on v1, upload them first
    news = []
    for i in range(6):
        _, v = push(c, h, P, "side%d" % i, "", {"A": ("x%d" % i).encode()}, [v1])
        news.append(v)

    def go(v):
        return c.put("/api/projects/aya/hero/branches/main", json={"old": v1, "new": v}, headers=h).status_code

    with ThreadPoolExecutor(6) as ex:
        codes = list(ex.map(go, news))
    assert sorted(codes) == [200] + [409] * 5
