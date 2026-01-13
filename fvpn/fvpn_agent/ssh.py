\
from __future__ import annotations

import os
import secrets
import string
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Tuple


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _rand_str(n: int) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def generate_username(prefix: str = "u", length: int = 8) -> str:
    return f"{prefix}{_rand_str(max(4, length))}"


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def user_exists(username: str) -> bool:
    try:
        import pwd
        pwd.getpwnam(username)
        return True
    except Exception:
        return False


def create_ssh_user(username: str, password: str, days: int) -> datetime:
    """
    Creates Linux user for SSH and sets expiry.
    Returns expires_at (UTC).
    """
    expires = (utcnow() + timedelta(days=days)).date().isoformat()

    # Create user (no home dir to keep it lightweight)
    # NOTE: This is a server-side tool; requires root.
    subprocess.run(["useradd", "-M", "-s", "/bin/bash", "-e", expires, username], check=True)
    subprocess.run(["bash", "-lc", f"echo '{username}:{password}' | chpasswd"], check=True)

    return datetime.fromisoformat(expires).replace(tzinfo=timezone.utc)
