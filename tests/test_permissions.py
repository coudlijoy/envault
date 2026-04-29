import json
import pytest
from pathlib import Path
from envault.permissions import PermissionManager, PermissionError


@pytest.fixture
def permissions_file(tmp_path):
    return tmp_path / ".envault_permissions"


@pytest.fixture
def manager(permissions_file):
    return PermissionManager(permissions_file)


class TestPermissionManagerInit:
    def test_creates_empty_permissions_when_no_file(self, permissions_file):
        pm = PermissionManager(permissions_file)
        assert pm.list_users() == []

    def test_loads_existing_permissions(self, permissions_file):
        permissions_file.write_text(json.dumps({"alice": "admin"}))
        pm = PermissionManager(permissions_file)
        assert pm.get_role("alice") == "admin"

    def test_raises_on_invalid_json(self, permissions_file):
        permissions_file.write_text("not json")
        with pytest.raises(PermissionError, match="Failed to load permissions"):
            PermissionManager(permissions_file)


class TestAddUser:
    def test_add_user_with_valid_role(self, manager, permissions_file):
        manager.add_user("alice", "admin")
        assert manager.get_role("alice") == "admin"

    def test_add_user_persists_to_file(self, manager, permissions_file):
        manager.add_user("bob", "viewer")
        data = json.loads(permissions_file.read_text())
        assert data["bob"] == "viewer"

    def test_add_user_invalid_role_raises(self, manager):
        with pytest.raises(PermissionError, match="Invalid role"):
            manager.add_user("charlie", "superuser")

    def test_all_valid_roles_accepted(self, manager):
        for role in ["admin", "editor", "viewer"]:
            manager.add_user(f"user_{role}", role)
            assert manager.get_role(f"user_{role}") == role


class TestRemoveUser:
    def test_remove_existing_user(self, manager):
        manager.add_user("alice", "editor")
        manager.remove_user("alice")
        assert manager.get_role("alice") is None

    def test_remove_nonexistent_user_raises(self, manager):
        with pytest.raises(PermissionError, match="not found"):
            manager.remove_user("ghost")


class TestCapabilities:
    def test_admin_can_manage_users(self, manager):
        manager.add_user("alice", "admin")
        assert manager.can("alice", "manage_users") is True

    def test_viewer_cannot_write(self, manager):
        manager.add_user("bob", "viewer")
        assert manager.can("bob", "write") is False

    def test_editor_can_lock_and_unlock(self, manager):
        manager.add_user("carol", "editor")
        assert manager.can("carol", "lock") is True
        assert manager.can("carol", "unlock") is True

    def test_unknown_user_cannot_do_anything(self, manager):
        assert manager.can("unknown", "read") is False

    def test_require_raises_for_insufficient_role(self, manager):
        manager.add_user("dave", "viewer")
        with pytest.raises(PermissionError, match="cannot perform"):
            manager.require("dave", "write")

    def test_require_raises_for_unknown_user(self, manager):
        with pytest.raises(PermissionError, match="no permissions"):
            manager.require("nobody", "read")

    def test_require_passes_for_authorized_user(self, manager):
        manager.add_user("eve", "admin")
        manager.require("eve", "manage_users")  # should not raise
