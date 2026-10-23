import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  pw_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0,
  created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  created REAL NOT NULL,
  UNIQUE(owner_id, name)
);
CREATE TABLE IF NOT EXISTS members (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('read','write')),
  PRIMARY KEY (project_id, user_id)
);
-- A branch is just a name and the commit it points at ('' = no commits yet).
CREATE TABLE IF NOT EXISTS branches (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  commit_id TEXT NOT NULL,
  updated REAL NOT NULL,
  PRIMARY KEY (project_id, name)
);
-- Which files (by fingerprint) each project has. The files themselves are on disk.
CREATE TABLE IF NOT EXISTS objects (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  hash TEXT NOT NULL,
  size INTEGER NOT NULL,
  PRIMARY KEY (project_id, hash)
);
CREATE TABLE IF NOT EXISTS activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id),
  action TEXT NOT NULL,
  detail TEXT NOT NULL,
  ts REAL NOT NULL
);
"""


def connect(path):
    # autocommit mode; branch moves open an explicit transaction
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init(path):
    conn = connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.close()
