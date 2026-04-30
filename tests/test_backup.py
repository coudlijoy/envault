"""Tests for envault.backup module."""

import json
import pytest
from pathlib import Path
from envault.backup import BackupManager, BackupError


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def vault_file(tmp_dir):
    f = tmp_dir / "test.env.enc"
    f.write_bytes(b"encrypted-content-abc123")
    return f


@pytest.fixture
def manager(tmp_dir):
    return BackupManager(str(tmp_dir))


class TestBackupManagerCreate:
    def test_creates_backup_file(self, manager, vault_file, tmp_dir):
        dest = manager.create_backup(str(vault_file))
        assert Path(dest).exists()

    def test_backup_has_correct_content(self, manager, vault_file):
        dest = manager.create_backup(str(vault_file))
        assert Path(dest).read_bytes() == b"encrypted-content-abc123"

    def test_backup_updates_index(self, manager, vault_file, tmp_dir):
        manager.create_backup(str(vault_file))
        index_path = tmp_dir / ".envault_backups" / "index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())
        assert len(index) == 1

    def test_backup_stores_label(self, manager, vault_file, tmp_dir):
        manager.create_backup(str(vault_file), label="pre-deploy")
        index = manager._load_index()
        assert index[0]["label"] == "pre-deploy"

    def test_raises_if_vault_not_found(self, manager, tmp_dir):
        with pytest.raises(BackupError, match="not found"):
            manager.create_backup(str(tmp_dir / "missing.enc"))

    def test_max_backups_enforced(self, manager, vault_file):
        for _ in range(12):
            manager.create_backup(str(vault_file))
        index = manager._load_index()
        assert len(index) <= BackupManager.MAX_BACKUPS


class TestBackupManagerList:
    def test_returns_empty_list_when_no_backups(self, manager):
        assert manager.list_backups() == []

    def test_returns_entries_after_backup(self, manager, vault_file):
        manager.create_backup(str(vault_file))
        entries = manager.list_backups()
        assert len(entries) == 1
        assert "timestamp" in entries[0]
        assert "file" in entries[0]


class TestBackupManagerRestore:
    def test_restores_file_to_target(self, manager, vault_file, tmp_dir):
        manager.create_backup(str(vault_file))
        entries = manager.list_backups()
        backup_name = entries[0]["file"]
        target = tmp_dir / "restored.env.enc"
        manager.restore_backup(backup_name, str(target))
        assert target.read_bytes() == b"encrypted-content-abc123"

    def test_raises_if_backup_not_found(self, manager, tmp_dir):
        with pytest.raises(BackupError, match="not found"):
            manager.restore_backup("nonexistent.bak", str(tmp_dir / "out.enc"))
