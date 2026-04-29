"""Tests for envault.export module."""

import json
import os
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.export import VaultExporter, ExportError


@pytest.fixture
def shared_key():
    return "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXQ="


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDB_URL=postgres://localhost/db\n")
    return str(p)


@pytest.fixture
def vault(tmp_path, shared_key, env_file):
    v = Vault(env_file, shared_key, vault_dir=str(tmp_path))
    v.lock()
    return v


@pytest.fixture
def exporter(vault):
    return VaultExporter(vault)


class TestExportBundle:
    def test_export_creates_bundle_file(self, exporter, tmp_path):
        out = str(tmp_path / "export" / "bundle.json")
        result = exporter.export_bundle(out)
        assert Path(result).exists()

    def test_export_bundle_is_valid_json(self, exporter, tmp_path):
        out = str(tmp_path / "bundle.json")
        exporter.export_bundle(out)
        with open(out) as f:
            data = json.load(f)
        assert "version" in data
        assert "data" in data
        assert "source" in data

    def test_export_bundle_version(self, exporter, tmp_path):
        out = str(tmp_path / "bundle.json")
        exporter.export_bundle(out)
        with open(out) as f:
            data = json.load(f)
        assert data["version"] == VaultExporter.BUNDLE_VERSION

    def test_export_raises_if_vault_missing(self, shared_key, tmp_path):
        env = str(tmp_path / ".env")
        v = Vault(env, shared_key, vault_dir=str(tmp_path))
        exporter = VaultExporter(v)
        with pytest.raises(ExportError, match="Vault file not found"):
            exporter.export_bundle(str(tmp_path / "bundle.json"))


class TestImportBundle:
    def test_import_restores_vault_file(self, exporter, tmp_path, shared_key):
        bundle_path = str(tmp_path / "bundle.json")
        exporter.export_bundle(bundle_path)

        new_env = str(tmp_path / "new" / ".env")
        new_vault = Vault(new_env, shared_key, vault_dir=str(tmp_path / "new"))
        new_exporter = VaultExporter(new_vault)
        result = new_exporter.import_bundle(bundle_path)
        assert Path(result).exists()

    def test_import_raises_on_missing_bundle(self, exporter, tmp_path):
        with pytest.raises(ExportError, match="Bundle file not found"):
            exporter.import_bundle(str(tmp_path / "nonexistent.json"))

    def test_import_raises_on_existing_vault_without_overwrite(
        self, exporter, tmp_path
    ):
        bundle_path = str(tmp_path / "bundle.json")
        exporter.export_bundle(bundle_path)
        with pytest.raises(ExportError, match="Vault already exists"):
            exporter.import_bundle(bundle_path, overwrite=False)

    def test_import_overwrites_when_flag_set(self, exporter, tmp_path):
        bundle_path = str(tmp_path / "bundle.json")
        exporter.export_bundle(bundle_path)
        result = exporter.import_bundle(bundle_path, overwrite=True)
        assert Path(result).exists()

    def test_import_raises_on_invalid_json(self, exporter, tmp_path):
        bad_bundle = tmp_path / "bad.json"
        bad_bundle.write_text("not valid json")
        with pytest.raises(ExportError, match="Failed to read bundle"):
            exporter.import_bundle(str(bad_bundle))

    def test_import_raises_on_wrong_version(self, exporter, tmp_path):
        bundle_path = str(tmp_path / "bundle.json")
        with open(bundle_path, "w") as f:
            json.dump({"version": 99, "data": "abc", "source": "x"}, f)
        with pytest.raises(ExportError, match="Unsupported bundle version"):
            exporter.import_bundle(bundle_path)
