"""Export and import utilities for envault vault files."""

import json
import os
import base64
from pathlib import Path
from typing import Optional

from envault.vault import Vault, VaultError


class ExportError(Exception):
    """Raised when export/import operations fail."""
    pass


class VaultExporter:
    """Handles exporting and importing encrypted vault bundles."""

    BUNDLE_VERSION = 1

    def __init__(self, vault: Vault):
        self.vault = vault

    def export_bundle(self, output_path: str) -> str:
        """Export the encrypted vault as a portable JSON bundle.

        Args:
            output_path: Path where the bundle file will be written.

        Returns:
            The resolved path to the written bundle file.

        Raises:
            ExportError: If the vault file does not exist or export fails.
        """
        vault_path = Path(self.vault.vault_path)
        if not vault_path.exists():
            raise ExportError(f"Vault file not found: {vault_path}")

        try:
            with open(vault_path, "rb") as f:
                raw = f.read()

            bundle = {
                "version": self.BUNDLE_VERSION,
                "source": vault_path.name,
                "data": base64.b64encode(raw).decode("utf-8"),
            }

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as f:
                json.dump(bundle, f, indent=2)

            return str(out.resolve())
        except (OSError, ValueError) as exc:
            raise ExportError(f"Export failed: {exc}") from exc

    def import_bundle(self, bundle_path: str, overwrite: bool = False) -> str:
        """Import an encrypted vault bundle.

        Args:
            bundle_path: Path to the bundle file to import.
            overwrite: If True, overwrite an existing vault file.

        Returns:
            The resolved path to the restored vault file.

        Raises:
            ExportError: If the bundle is invalid or the vault already exists.
        """
        bundle_file = Path(bundle_path)
        if not bundle_file.exists():
            raise ExportError(f"Bundle file not found: {bundle_path}")

        try:
            with open(bundle_file, "r") as f:
                bundle = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise ExportError(f"Failed to read bundle: {exc}") from exc

        if bundle.get("version") != self.BUNDLE_VERSION:
            raise ExportError(
                f"Unsupported bundle version: {bundle.get('version')}"
            )

        vault_path = Path(self.vault.vault_path)
        if vault_path.exists() and not overwrite:
            raise ExportError(
                f"Vault already exists at {vault_path}. Use overwrite=True to replace."
            )

        try:
            raw = base64.b64decode(bundle["data"])
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            with open(vault_path, "wb") as f:
                f.write(raw)
            return str(vault_path.resolve())
        except (KeyError, base64.binascii.Error, OSError) as exc:
            raise ExportError(f"Import failed: {exc}") from exc
