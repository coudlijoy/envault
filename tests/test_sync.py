"""Tests for the SyncManager module."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envault.sync import SyncManager, SyncError
from envault.vault import Vault


@pytest.fixture
def shared_key():
    return "test-shared-key-1234567890abcdef"


@pytest.fixture
def shared_dir(tmp_path):
    d = tmp_path / "shared"
    d.mkdir()
    return d


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("API_KEY=secret\nDB_URL=postgres://localhost/db\n")
    return f


@pytest.fixture
def vault(tmp_path):
    return Vault(str(tmp_path))


@pytest.fixture
def sync_manager(shared_dir, vault):
    return SyncManager(str(shared_dir), vault)


class TestSyncManagerInit:
    def test_sets_shared_dir(self, sync_manager, shared_dir):
        assert sync_manager.shared_dir == shared_dir

    def test_sets_vault(self, sync_manager, vault):
        assert sync_manager.vault is vault


class TestPush:
    def test_push_creates_vault_in_shared_dir(self, sync_manager, shared_dir, env_file, shared_key):
        sync_manager.push(str(env_file), shared_key)
        assert (shared_dir / ".env.vault").exists()

    def test_push_raises_if_shared_dir_missing(self, vault, shared_key, env_file):
        manager = SyncManager("/nonexistent/path", vault)
        with pytest.raises(SyncError, match="Shared directory does not exist"):
            manager.push(str(env_file), shared_key)


class TestPull:
    def test_pull_decrypts_env_file(self, sync_manager, shared_dir, env_file, shared_key, tmp_path):
        sync_manager.push(str(env_file), shared_key)
        output = tmp_path / ".env.pulled"
        sync_manager.pull(shared_key, str(output))
        assert output.exists()
        content = output.read_text()
        assert "API_KEY=secret" in content

    def test_pull_raises_if_no_vault_in_shared_dir(self, sync_manager, shared_key):
        with pytest.raises(SyncError, match="No vault file found"):
            sync_manager.pull(shared_key)


class TestIsOutdated:
    def test_not_outdated_when_no_shared_vault(self, sync_manager):
        assert sync_manager.is_outdated() is False

    def test_outdated_when_local_vault_missing(self, sync_manager, shared_dir, env_file, shared_key):
        sync_manager.push(str(env_file), shared_key)
        # Remove local vault copy
        local = Path(sync_manager.vault.vault_path)
        if local.exists():
            local.unlink()
        assert sync_manager.is_outdated() is True

    def test_not_outdated_after_pull(self, sync_manager, shared_dir, env_file, shared_key):
        sync_manager.push(str(env_file), shared_key)
        sync_manager.pull(shared_key)
        assert sync_manager.is_outdated() is False
