"""OAuth tokens never land world-readable, and prefer the OS keychain."""

import json
import os
import stat

import pytest

import token_store


@pytest.fixture
def tmp_token(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    monkeypatch.setattr(token_store, "TOKEN_FILE", path)
    return path


def test_file_fallback_is_owner_only(tmp_token, monkeypatch):
    monkeypatch.setenv("AGENT_ADAM_TOKEN_STORE", "file")
    tmp_token.write_text("{}")
    os.chmod(tmp_token, 0o644)  # a pre-existing, too-open file gets tightened
    assert token_store.save({"refresh_token": "r"}) == str(tmp_token)
    assert stat.S_IMODE(tmp_token.stat().st_mode) == 0o600
    assert token_store.load() == {"refresh_token": "r"}


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def get_password(self, s, a):
        return self.store.get((s, a))

    def set_password(self, s, a, v):
        self.store[(s, a)] = v

    def delete_password(self, s, a):
        self.store.pop((s, a), None)


def test_keyring_is_used_and_plaintext_file_is_migrated_away(tmp_token, monkeypatch):
    kr = FakeKeyring()
    monkeypatch.setattr(token_store, "_keyring", lambda: kr)
    tmp_token.write_text(json.dumps({"refresh_token": "legacy"}))
    assert token_store.load() == {"refresh_token": "legacy"}
    assert not tmp_token.exists()  # migrated into the keychain
    assert json.loads(kr.store[("agent-adam", "google-oauth-token")])["refresh_token"] == "legacy"
    token_store.clear()
    assert token_store.load() is None
