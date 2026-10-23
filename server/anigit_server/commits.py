"""A commit record is a small JSON file stored like any other object.

{"parents": ["<commit hash>", ...],          # two parents = a merge
 "files":   {"<path in the .kra>": "<hash>"}, # every file needed to rebuild the .kra
 "layers":  {"<layer id>": "<hash>", ...},    # optional, informational: one fingerprint per layer
 "preview": "<hash>" or null,
 "author": "...", "note": "...", "timestamp": 123.0}

The server reads only parents, files, layers and preview. It never opens layer files.
Everything in parents, files and preview must already be uploaded before a branch can point here.
"""
import json
import re

HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_commit(data: bytes) -> dict:
    try:
        c = json.loads(data)
    except Exception:
        raise ValueError("The commit record is not valid JSON.")
    if not isinstance(c, dict):
        raise ValueError("The commit record must be a JSON object.")
    parents = c.get("parents")
    files = c.get("files")
    layers = c.get("layers", {})
    if not isinstance(parents, list) or not all(isinstance(p, str) and HASH_RE.match(p) for p in parents):
        raise ValueError("The commit record's 'parents' must be a list of fingerprints.")
    if not isinstance(files, dict) or not all(isinstance(v, str) and HASH_RE.match(v) for v in files.values()):
        raise ValueError("The commit record's 'files' must map file paths to fingerprints.")
    if not isinstance(layers, dict) or not all(isinstance(v, str) and HASH_RE.match(v) for v in layers.values()):
        raise ValueError("The commit record's 'layers' must map layer ids to fingerprints.")
    prev = c.get("preview")
    if prev is not None and not (isinstance(prev, str) and HASH_RE.match(prev)):
        raise ValueError("The commit record's 'preview' must be a fingerprint or null.")
    return c


def referenced(c: dict) -> list:
    refs = list(c["parents"]) + list(c["files"].values())
    if c.get("preview"):
        refs.append(c["preview"])
    return sorted(set(refs))


def is_ancestor(store, project_id, ancestor, descendant, limit=200000) -> bool:
    """True if `ancestor` can be reached by walking back from `descendant`."""
    seen, stack = set(), [descendant]
    while stack and len(seen) < limit:
        cur = stack.pop()
        if cur == ancestor:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        try:
            stack.extend(parse_commit(store.path(project_id, cur).read_bytes())["parents"])
        except (OSError, ValueError):
            continue
    return False
