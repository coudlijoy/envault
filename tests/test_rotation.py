"""Tests for envault.rotation module."""

import json
import pytest
from pathlib import Path
from envault.crypto import generate_key
from envault.vault import Vault
from envault.rotation import KeyRotator, RotationError


@pytest.fixture
def shared_key():
    return generate_key()


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env.vault"
    return f


@pytest.fixture
def vault(env_file, shared_key):
    v = Vault(str(env_file), shared_key)
    v.lock("SECRET=hello\nDB_URL=postgres://localhost/db")
    return v


@pytest.fixture
def rotator(env_file, vault):
    return KeyRotator(str(env_file))


class TestKeyRotatorRotate:
    def test_rotate_returns_new_key(self, rotator, env_file, shared_key):
        new_key = rotator.rotate(shared_key)
        assert isinstance(new_key, str)
        assert new_key != shared_key

    def test_rotated_vault_decryptable_with_new_key(self, rotator, env_file, shared_key):
        new_key = rotator.rotate(shared_key)
        v = Vault(str(env_file), new_key)
        content = v.unlock()
        assert "SECRET=hello" in content

    def test_old_key_no_longer_works(self, rotator, env_file, shared_key):
        new_key = rotator.rotate(shared_key)
        v = Vault(str(env_file), shared_key)
        with pytest.raises(Exception):
            v.unlock()

    def test_rotate_accepts_custom_new_key(self, rotator, env_file, shared_key):
        custom_key = generate_key()
        returned_key = rotator.rotate(shared_key, new_key=custom_key)
        assert returned_key == custom_key

    def test_rotate_raises_if_vault_missing(self, tmp_path, shared_key):
        rotator = KeyRotator(str(tmp_path / "nonexistent.vault"))
        with pytest.raises(RotationError, match="Vault not found"):
            rotator.rotate(shared_key)

    def test_rotate_raises_on_wrong_current_key(self, rotator, env_file):
        wrong_key = generate_key()
        with pytest.raises(RotationError, match="Failed to unlock"):
            rotator.rotate(wrong_key)


class TestKeyRotatorHistory:
    def test_rotation_history_empty_before_rotation(self, rotator):
        assert rotator.rotation_history() == []

    def test_rotation_history_records_event(self, rotator, shared_key):
        rotator.rotate(shared_key)
        history = rotator.rotation_history()
        assert len(history) == 1
        assert "rotated_at" in history[0]

    def test_rotation_history_accumulates(self, rotator, shared_key):
        key1 = rotator.rotate(shared_key)
        rotator.rotate(key1)
        history = rotator.rotation_history()
        assert len(history) == 2
