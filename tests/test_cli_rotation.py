"""Tests for CLI key rotation commands."""

import pytest
from click.testing import CliRunner
from envault.crypto import generate_key
from envault.vault import Vault
from envault.cli_rotation import rotation


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def shared_key():
    return generate_key()


@pytest.fixture
def sample_vault(tmp_path, shared_key):
    vault_path = tmp_path / ".env.vault"
    v = Vault(str(vault_path), shared_key)
    v.lock("API_KEY=secret123")
    return str(vault_path)


class TestRotateCommand:
    def test_rotate_succeeds_and_prints_new_key(self, runner, sample_vault, shared_key):
        result = runner.invoke(rotation, ["rotate", sample_vault, "--key", shared_key])
        assert result.exit_code == 0
        assert "Key rotated successfully" in result.output
        assert "New key:" in result.output

    def test_rotate_with_custom_new_key(self, runner, sample_vault, shared_key):
        new_key = generate_key()
        result = runner.invoke(
            rotation, ["rotate", sample_vault, "--key", shared_key, "--new-key", new_key]
        )
        assert result.exit_code == 0
        assert new_key in result.output

    def test_rotate_fails_with_wrong_key(self, runner, sample_vault):
        wrong_key = generate_key()
        result = runner.invoke(rotation, ["rotate", sample_vault, "--key", wrong_key])
        assert result.exit_code != 0
        assert "Rotation failed" in result.output

    def test_rotate_fails_with_missing_vault(self, runner, tmp_path, shared_key):
        missing = str(tmp_path / "missing.vault")
        result = runner.invoke(rotation, ["rotate", missing, "--key", shared_key])
        assert result.exit_code != 0
        assert "Rotation failed" in result.output


class TestHistoryCommand:
    def test_history_empty_before_rotation(self, runner, sample_vault, shared_key):
        result = runner.invoke(rotation, ["history", sample_vault])
        assert result.exit_code == 0
        assert "No rotation history found" in result.output

    def test_history_shows_event_after_rotation(self, runner, sample_vault, shared_key):
        runner.invoke(rotation, ["rotate", sample_vault, "--key", shared_key])
        result = runner.invoke(rotation, ["history", sample_vault])
        assert result.exit_code == 0
        assert "Rotation history" in result.output
        assert "1." in result.output
