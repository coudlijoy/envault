"""Tests for envault.diff module."""

import pytest
from pathlib import Path

from envault.crypto import generate_key
from envault.vault import Vault
from envault.diff import DiffError, DiffResult, VaultDiff, _parse_env


@pytest.fixture
def shared_key():
    return generate_key()


@pytest.fixture
def vault_content():
    return "DB_HOST=localhost\nDB_PORT=5432\nSECRET=old_secret\n"


@pytest.fixture
def vault(tmp_path, shared_key, vault_content):
    v = Vault(tmp_path / ".env.vault")
    v.lock(vault_content, shared_key)
    return v


@pytest.fixture
def vault_diff(vault, shared_key):
    return VaultDiff(vault, shared_key)


class TestParseEnv:
    def test_parses_key_value_pairs(self):
        result = _parse_env("FOO=bar\nBAZ=qux\n")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments(self):
        result = _parse_env("# comment\nFOO=bar\n")
        assert "# comment" not in result
        assert result["FOO"] == "bar"

    def test_ignores_blank_lines(self):
        result = _parse_env("\nFOO=bar\n\n")
        assert result == {"FOO": "bar"}

    def test_handles_empty_string(self):
        assert _parse_env("") == {}


class TestDiffResult:
    def test_has_changes_false_when_empty(self):
        assert not DiffResult().has_changes

    def test_has_changes_true_with_added(self):
        dr = DiffResult(added={"NEW_KEY": "val"})
        assert dr.has_changes

    def test_summary_no_changes(self):
        assert DiffResult().summary() == "No changes."

    def test_summary_shows_added(self):
        dr = DiffResult(added={"NEW_KEY": "val"})
        assert "+ NEW_KEY=val" in dr.summary()

    def test_summary_shows_removed(self):
        dr = DiffResult(removed={"OLD_KEY": "val"})
        assert "- OLD_KEY=val" in dr.summary()

    def test_summary_shows_modified(self):
        dr = DiffResult(modified={"KEY": ("old", "new")})
        assert "~ KEY" in dr.summary()


class TestVaultDiff:
    def test_no_changes_when_identical(self, vault_diff, tmp_path, vault_content):
        env_file = tmp_path / ".env"
        env_file.write_text(vault_content)
        result = vault_diff.diff_with_file(env_file)
        assert not result.has_changes

    def test_detects_added_key(self, vault_diff, tmp_path, vault_content):
        env_file = tmp_path / ".env"
        env_file.write_text(vault_content + "NEW_VAR=hello\n")
        result = vault_diff.diff_with_file(env_file)
        assert "NEW_VAR" in result.added

    def test_detects_removed_key(self, vault_diff, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("DB_HOST=localhost\n")
        result = vault_diff.diff_with_file(env_file)
        assert "DB_PORT" in result.removed
        assert "SECRET" in result.removed

    def test_detects_modified_key(self, vault_diff, tmp_path, vault_content):
        env_file = tmp_path / ".env"
        env_file.write_text(vault_content.replace("old_secret", "new_secret"))
        result = vault_diff.diff_with_file(env_file)
        assert "SECRET" in result.modified
        assert result.modified["SECRET"] == ("old_secret", "new_secret")

    def test_raises_diff_error_for_missing_file(self, vault_diff, tmp_path):
        with pytest.raises(DiffError, match="File not found"):
            vault_diff.diff_with_file(tmp_path / "nonexistent.env")

    def test_raises_diff_error_on_bad_key(self, vault, tmp_path):
        bad_diff = VaultDiff(vault, generate_key())
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n")
        with pytest.raises(DiffError, match="Failed to unlock vault"):
            bad_diff.diff_with_file(env_file)
