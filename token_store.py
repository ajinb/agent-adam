"""Where the Google OAuth token lives between runs.

The token carries a refresh token: long-lived access to the user's calendar, mail
and tasks. It is stored in the operating system's keychain (macOS Keychain,
Windows Credential Manager, Secret Service on Linux) through `keyring` when a
secure backend is available. Otherwise it falls back to `token.json` written with
owner-only permissions (0600), never the world-readable default.

    AGENT_ADAM_TOKEN_STORE=keyring | file | auto   (default: auto)
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path

SERVICE = "agent-adam"
ACCOUNT = "google-oauth-token"
TOKEN_FILE = Path(__file__).resolve().parent / "token.json"


def _keyring():
    mode = os.getenv("AGENT_ADAM_TOKEN_STORE", "auto").lower()
    if mode == "file":
        return None
    try:
        import keyring
        from keyring.backends import fail
    except ImportError:
        if mode == "keyring":
            raise RuntimeError("AGENT_ADAM_TOKEN_STORE=keyring but `keyring` is not installed") from None
        return None
    backend = keyring.get_keyring()
    if isinstance(backend, fail.Keyring) or "plaintext" in type(backend).__name__.lower():
        if mode == "keyring":
            raise RuntimeError("no secure keyring backend is available on this machine")
        return None
    return keyring


def load() -> dict | None:
    kr = _keyring()
    if kr is not None:
        raw = kr.get_password(SERVICE, ACCOUNT)
        if raw:
            return json.loads(raw)
        if TOKEN_FILE.exists():  # one-time migration off the plaintext file
            data = json.loads(TOKEN_FILE.read_text())
            save(data)
            return data
        return None
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def save(data: dict) -> str:
    """Persist the token; returns where it went ("keyring" or the file path)."""
    payload = json.dumps(data)
    kr = _keyring()
    if kr is not None:
        kr.set_password(SERVICE, ACCOUNT, payload)
        TOKEN_FILE.unlink(missing_ok=True)
        return "keyring"
    # O_CREAT with 0600 so the file is never readable by others, even briefly.
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(payload)
    os.chmod(TOKEN_FILE, 0o600)  # tighten a pre-existing file too
    return str(TOKEN_FILE)


def clear() -> None:
    kr = _keyring()
    if kr is not None:
        with contextlib.suppress(Exception):  # an absent entry is fine
            kr.delete_password(SERVICE, ACCOUNT)
    TOKEN_FILE.unlink(missing_ok=True)
