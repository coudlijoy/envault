"""Tests for envault.cli_hooks CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_hooks import hooks


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_script(tmp_path):
    script = tmp_path / "hook.sh"
    script.write_text("#!/bin/sh\necho 'done'\n")
    script.chmod(0o755)
    return script


class TestRegisterCommand:
    def test_register_succeeds(self, runner, sample_script, tmp_path):
        hooks_dir = tmp_path / "hooks"
        result = runner.invoke(
            hooks,
            ["register", "post-lock", str(sample_script), "--hooks-dir", str(hooks_dir)],
        )
        assert result.exit_code == 0
        assert "Hook registered" in result.output

    def test_register_missing_script_fails(self, runner, tmp_path):
        hooks_dir = tmp_path / "hooks"
        result = runner.invoke(
            hooks,
            ["register", "post-lock", "/nonexistent/script.sh", "--hooks-dir", str(hooks_dir)],
        )
        assert result.exit_code != 0


class TestListCommand:
    def test_list_empty(self, runner, tmp_path):
        result = runner.invoke(hooks, ["list", "--hooks-dir", str(tmp_path / "hooks")])
        assert result.exit_code == 0
        assert "No hooks registered" in result.output

    def test_list_shows_registered_hooks(self, runner, sample_script, tmp_path):
        hooks_dir = tmp_path / "hooks"
        runner.invoke(
            hooks,
            ["register", "pre-sync", str(sample_script), "--hooks-dir", str(hooks_dir)],
        )
        result = runner.invoke(hooks, ["list", "--hooks-dir", str(hooks_dir)])
        assert result.exit_code == 0
        assert "pre-sync" in result.output


class TestRemoveCommand:
    def test_remove_existing_hook(self, runner, sample_script, tmp_path):
        hooks_dir = tmp_path / "hooks"
        runner.invoke(
            hooks,
            ["register", "post-sync", str(sample_script), "--hooks-dir", str(hooks_dir)],
        )
        result = runner.invoke(hooks, ["remove", "post-sync", "--hooks-dir", str(hooks_dir)])
        assert result.exit_code == 0
        assert "Hook removed" in result.output

    def test_remove_nonexistent_hook(self, runner, tmp_path):
        result = runner.invoke(
            hooks, ["remove", "post-sync", "--hooks-dir", str(tmp_path / "hooks")]
        )
        assert result.exit_code == 0
        assert "No hook registered" in result.output
