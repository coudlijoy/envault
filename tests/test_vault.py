"""Tests for the Vault class in envault/vault.py."""

import os
import pytest
import tempfile
from pathlib import Path

from envault.vault import Vault, VaultError
from envault.crypto import generate_key


@pytest.fixture
def shared_key():
    """Generate a fresh shared key for each test."""
    return generate_key()


@pytest.fixture
def sample_env_content():
    """Sample .env file content for testing."""
    return (
        "DATABASE_URL=postgres://user:password@localhost:5432/mydb\n"
        "SECRET_KEY=supersecretvalue\n"
        "DEBUG=True\n"
        "API_KEY=abc123xyz\n"
    )


@pytest.fixture
def env_file(tmp_path, sample_env_content):
    """Create a temporary .env file with sample content."""
    env_path = tmp_path / ".env"
    env_path.write_text(sample_env_content)
    return env_path


@pytest.fixture
def vault(env_file, shared_key):
    """Create a Vault instance pointing at the temp .env file."""
    return Vault(env_file, shared_key)


class TestVaultInit:
    def test_vault_stores_env_path(self, vault, env_file):
        assert vault.env_path == Path(env_file)

    def test_vault_stores_key(self, vault, shared_key):
        assert vault.key == shared_key

    def test_vault_accepts_string_path(self, env_file, shared_key):
        v = Vault(str(env_file), shared_key)
        assert v.env_path == Path(env_file)

    def test_vault_raises_if_env_missing(self, tmp_path, shared_key):
        missing = tmp_path / "nonexistent.env"
        with pytest.raises(VaultError, match="not found"):
            Vault(missing, shared_key)


class TestVaultLock:
    def test_lock_creates_vault_file(self, vault, env_file):
        vault.lock()
        vault_file = env_file.with_suffix(".vault")
        assert vault_file.exists()

    def test_lock_vault_file_is_not_plaintext(self, vault, env_file, sample_env_content):
        vault.lock()
        vault_file = env_file.with_suffix(".vault")
        encrypted_content = vault_file.read_text()
        assert "DATABASE_URL" not in encrypted_content
        assert "SECRET_KEY" not in encrypted_content

    def test_lock_returns_vault_path(self, vault, env_file):
        result = vault.lock()
        assert result == env_file.with_suffix(".vault")

    def test_lock_twice_overwrites(self, vault, env_file):
        vault.lock()
        vault_file = env_file.with_suffix(".vault")
        first_content = vault_file.read_bytes()
        vault.lock()
        second_content = vault_file.read_bytes()
        # Each encryption produces a different ciphertext due to random IV
        assert first_content != second_content


class TestVaultUnlock:
    def test_unlock_restores_env_content(self, vault, env_file, sample_env_content):
        vault.lock()
        # Remove the original .env to simulate a fresh checkout
        env_file.unlink()
        vault.unlock()
        assert env_file.read_text() == sample_env_content

    def test_unlock_requires_vault_file(self, vault, env_file):
        # No .vault file created yet
        with pytest.raises(VaultError, match="vault file"):
            vault.unlock()

    def test_unlock_fails_with_wrong_key(self, env_file, shared_key, sample_env_content):
        vault = Vault(env_file, shared_key)
        vault.lock()
        env_file.unlink()

        wrong_key = generate_key()
        bad_vault = Vault.__new__(Vault)
        bad_vault.env_path = Path(env_file)
        bad_vault.key = wrong_key

        with pytest.raises(VaultError, match="[Dd]ecrypt"):
            bad_vault.unlock()

    def test_roundtrip_preserves_content(self, vault, env_file, sample_env_content):
        vault.lock()
        env_file.unlink()
        vault.unlock()
        assert env_file.read_text() == sample_env_content


class TestVaultStatus:
    def test_status_unlocked_when_only_env_exists(self, vault):
        status = vault.status()
        assert status["has_env"] is True
        assert status["has_vault"] is False

    def test_status_locked_after_lock(self, vault, env_file):
        vault.lock()
        status = vault.status()
        assert status["has_vault"] is True

    def test_status_both_present(self, vault, env_file):
        vault.lock()
        # .env still exists alongside .vault
        status = vault.status()
        assert status["has_env"] is True
        assert status["has_vault"] is True
