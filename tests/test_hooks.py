"""Tests for envault.hooks module."""

import stat
import pytest
from pathlib import Path
from envault.hooks import HookManager, HookError, HOOK_EVENTS


@pytest.fixture
def hooks_dir(tmp_path):
    return tmp_path / "hooks"


@pytest.fixture
def manager(hooks_dir):
    return HookManager(hooks_dir)


@pytest.fixture
def sample_script(tmp_path):
    script = tmp_path / "myhook.sh"
    script.write_text("#!/bin/sh\necho 'hook ran'\n")
    script.chmod(0o755)
    return script


class TestHookManagerRegister:
    def test_register_creates_hooks_dir(self, manager, hooks_dir, sample_script):
        manager.register("post-lock", sample_script)
        assert hooks_dir.exists()

    def test_register_copies_script(self, manager, hooks_dir, sample_script):
        manager.register("post-lock", sample_script)
        assert (hooks_dir / "post-lock").exists()

    def test_registered_script_is_executable(self, manager, hooks_dir, sample_script):
        manager.register("post-unlock", sample_script)
        hook_file = hooks_dir / "post-unlock"
        assert hook_file.stat().st_mode & stat.S_IXUSR

    def test_register_invalid_event_raises(self, manager, sample_script):
        with pytest.raises(HookError, match="Unknown hook event"):
            manager.register("invalid-event", sample_script)

    def test_register_missing_script_raises(self, manager, tmp_path):
        with pytest.raises(HookError, match="not found"):
            manager.register("pre-lock", tmp_path / "nonexistent.sh")


class TestHookManagerRun:
    def test_run_returns_none_when_no_hook(self, manager):
        result = manager.run("pre-lock")
        assert result is None

    def test_run_executes_hook_and_returns_output(self, manager, sample_script):
        manager.register("post-sync", sample_script)
        output = manager.run("post-sync")
        assert output == "hook ran"

    def test_run_raises_on_failing_hook(self, manager, tmp_path):
        bad_script = tmp_path / "bad.sh"
        bad_script.write_text("#!/bin/sh\nexit 1\n")
        bad_script.chmod(0o755)
        manager.register("pre-sync", bad_script)
        with pytest.raises(HookError, match="failed"):
            manager.run("pre-sync")

    def test_run_invalid_event_raises(self, manager):
        with pytest.raises(HookError, match="Unknown hook event"):
            manager.run("bogus-event")


class TestHookManagerList:
    def test_list_empty_when_no_hooks_dir(self, manager):
        assert manager.list_hooks() == []

    def test_list_returns_registered_events(self, manager, sample_script):
        manager.register("pre-lock", sample_script)
        manager.register("post-unlock", sample_script)
        registered = manager.list_hooks()
        assert "pre-lock" in registered
        assert "post-unlock" in registered


class TestHookManagerRemove:
    def test_remove_existing_hook(self, manager, hooks_dir, sample_script):
        manager.register("pre-lock", sample_script)
        result = manager.remove("pre-lock")
        assert result is True
        assert not (hooks_dir / "pre-lock").exists()

    def test_remove_nonexistent_hook_returns_false(self, manager):
        result = manager.remove("pre-lock")
        assert result is False
