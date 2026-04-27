"""Tests for the envault CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli
from envault.crypto import generate_key


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def shared_key():
    return generate_key()


@pytest.fixture
def sample_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=supersecret\n")
    return env_file


class TestKeygenCommand:
    def test_keygen_outputs_key(self, runner):
        result = runner.invoke(cli, ["keygen"])
        assert result.exit_code == 0
        assert "Generated key:" in result.output

    def test_keygen_key_is_unique(self, runner):
        result1 = runner.invoke(cli, ["keygen"])
        result2 = runner.invoke(cli, ["keygen"])
        key1 = result1.output.split("Generated key: ")[1].strip()
        key2 = result2.output.split("Generated key: ")[1].strip()
        assert key1 != key2


class TestLockCommand:
    def test_lock_creates_vault_file(self, runner, sample_env_file, shared_key):
        vault_path = sample_env_file.with_suffix(".vault")
        result = runner.invoke(cli, [
            "lock", str(sample_env_file),
            "--key", shared_key,
            "--output", str(vault_path)
        ])
        assert result.exit_code == 0
        assert vault_path.exists()

    def test_lock_shows_success_message(self, runner, sample_env_file, shared_key):
        result = runner.invoke(cli, [
            "lock", str(sample_env_file),
            "--key", shared_key
        ])
        assert result.exit_code == 0
        assert "Locked" in result.output

    def test_lock_fails_with_invalid_key(self, runner, sample_env_file):
        result = runner.invoke(cli, [
            "lock", str(sample_env_file),
            "--key", "not-a-valid-base64-key!@#"
        ])
        assert result.exit_code != 0


class TestUnlockCommand:
    def test_unlock_restores_env_file(self, runner, sample_env_file, shared_key, tmp_path):
        vault_path = tmp_path / ".env.vault"
        runner.invoke(cli, [
            "lock", str(sample_env_file),
            "--key", shared_key,
            "--output", str(vault_path)
        ])
        restored_path = tmp_path / ".env.restored"
        result = runner.invoke(cli, [
            "unlock", str(vault_path),
            "--key", shared_key,
            "--output", str(restored_path)
        ])
        assert result.exit_code == 0
        assert restored_path.read_text() == sample_env_file.read_text()

    def test_unlock_fails_with_wrong_key(self, runner, sample_env_file, shared_key, tmp_path):
        vault_path = tmp_path / ".env.vault"
        runner.invoke(cli, [
            "lock", str(sample_env_file),
            "--key", shared_key,
            "--output", str(vault_path)
        ])
        wrong_key = generate_key()
        result = runner.invoke(cli, [
            "unlock", str(vault_path),
            "--key", wrong_key
        ])
        assert result.exit_code != 0
