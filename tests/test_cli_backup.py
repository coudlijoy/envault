"""Tests for envault.cli_backup CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_backup import backup


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_file(tmp_path):
    f = tmp_path / "test.env.enc"
    f.write_bytes(b"encrypted-data")
    return f


class TestCreateCommand:
    def test_create_succeeds(self, runner, vault_file):
        result = runner.invoke(backup, ["create", str(vault_file)])
        assert result.exit_code == 0
        assert "Backup created" in result.output

    def test_create_with_label(self, runner, vault_file):
        result = runner.invoke(backup, ["create", str(vault_file), "--label", "v1"])
        assert result.exit_code == 0
        assert "Backup created" in result.output

    def test_create_fails_missing_vault(self, runner, tmp_path):
        missing = tmp_path / "ghost.enc"
        result = runner.invoke(backup, ["create", str(missing)])
        assert result.exit_code != 0
        assert "Error" in result.output


class TestListCommand:
    def test_list_empty(self, runner, tmp_path):
        result = runner.invoke(backup, ["list", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No backups found" in result.output

    def test_list_shows_entries(self, runner, vault_file):
        runner.invoke(backup, ["create", str(vault_file), "--label", "test"])
        project_dir = str(vault_file.parent)
        result = runner.invoke(backup, ["list", "--project-dir", project_dir])
        assert result.exit_code == 0
        assert "test" in result.output


class TestRestoreCommand:
    def test_restore_succeeds(self, runner, vault_file, tmp_path):
        runner.invoke(backup, ["create", str(vault_file)])
        project_dir = str(vault_file.parent)
        from envault.backup import BackupManager
        mgr = BackupManager(project_dir)
        backup_name = mgr.list_backups()[0]["file"]
        target = tmp_path / "restored.enc"
        result = runner.invoke(backup, ["restore", backup_name, str(target), "--project-dir", project_dir])
        assert result.exit_code == 0
        assert "Restored" in result.output
        assert target.read_bytes() == b"encrypted-data"

    def test_restore_fails_missing_backup(self, runner, tmp_path):
        result = runner.invoke(backup, ["restore", "ghost.bak", str(tmp_path / "out.enc"), "--project-dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "Error" in result.output
