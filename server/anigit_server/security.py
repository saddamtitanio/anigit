import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "scrypt$%d$%d$%d$%s$%s" % (_N, _R, _P, salt.hex(), dk.hex())


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, dk = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt),
                             n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(got.hex(), dk)
    except Exception:
        return False


DUMMY_HASH = hash_password("not-a-real-password")  # keeps timing similar for unknown users


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()   # only the digest is stored


class LoginLimiter:
    """Block an address+username after too many wrong passwords in 15 minutes."""

    def __init__(self, max_failures=10, window=900):
        self.max, self.window = max_failures, window
        self.fails = defaultdict(list)

    def blocked(self, key) -> bool:
        now = time.time()
        self.fails[key] = [t for t in self.fails[key] if now - t < self.window]
        return len(self.fails[key]) >= self.max

    def fail(self, key):
        self.fails[key].append(time.time())

    def reset(self, key):
        self.fails.pop(key, None)
