"""Tests for envault.template module."""

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.template import TemplateError, TemplateManager
from envault.crypto import generate_key


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def shared_key():
    return generate_key()


@pytest.fixture()
def env_file(tmp_path, shared_key):
    path = tmp_path / ".env"
    path.write_text("DB_HOST=localhost\nDB_PASS=secret\n# comment\nDEBUG=true\n")
    v = Vault(path)
    v.lock(shared_key)
    return path


@pytest.fixture()
def vault(env_file):
    return Vault(env_file)


@pytest.fixture()
def manager(vault):
    return TemplateManager(vault)


# ---------------------------------------------------------------------------
# export_template
# ---------------------------------------------------------------------------

class TestExportTemplate:
    def test_creates_output_file(self, manager, shared_key, tmp_path):
        out = tmp_path / ".env.example"
        manager.export_template(out, shared_key)
        assert out.exists()

    def test_values_replaced_with_placeholder(self, manager, shared_key, tmp_path):
        out = tmp_path / ".env.example"
        manager.export_template(out, shared_key)
        content = out.read_text()
        assert "<value>" in content
        assert "localhost" not in content
        assert "secret" not in content

    def test_keys_preserved(self, manager, shared_key, tmp_path):
        out = tmp_path / ".env.example"
        manager.export_template(out, shared_key)
        content = out.read_text()
        assert "DB_HOST=" in content
        assert "DB_PASS=" in content
        assert "DEBUG=" in content

    def test_comments_preserved(self, manager, shared_key, tmp_path):
        out = tmp_path / ".env.example"
        manager.export_template(out, shared_key)
        assert "# comment" in out.read_text()

    def test_returns_key_count(self, manager, shared_key, tmp_path):
        out = tmp_path / ".env.example"
        count = manager.export_template(out, shared_key)
        assert count == 3

    def test_raises_template_error_on_bad_key(self, manager, tmp_path):
        out = tmp_path / ".env.example"
        with pytest.raises(TemplateError):
            manager.export_template(out, generate_key())


# ---------------------------------------------------------------------------
# check_missing
# ---------------------------------------------------------------------------

class TestCheckMissing:
    def test_no_missing_when_env_matches(self, manager, shared_key, tmp_path):
        local = tmp_path / ".env.local"
        local.write_text("DB_HOST=x\nDB_PASS=y\nDEBUG=z\n")
        assert manager.check_missing(local, shared_key) == []

    def test_detects_missing_keys(self, manager, shared_key, tmp_path):
        local = tmp_path / ".env.local"
        local.write_text("DB_HOST=x\n")
        missing = manager.check_missing(local, shared_key)
        assert "DB_PASS" in missing
        assert "DEBUG" in missing

    def test_all_missing_when_file_absent(self, manager, shared_key, tmp_path):
        missing = manager.check_missing(tmp_path / "nonexistent.env", shared_key)
        assert set(missing) == {"DB_HOST", "DB_PASS", "DEBUG"}

    def test_raises_template_error_on_bad_key(self, manager, tmp_path):
        with pytest.raises(TemplateError):
            manager.check_missing(tmp_path / ".env", generate_key())
