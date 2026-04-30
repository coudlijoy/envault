"""Template support for .env files — generate .env.example from encrypted vault."""

import re
from pathlib import Path
from typing import Optional

from envault.vault import Vault, VaultError


class TemplateError(Exception):
    pass


class TemplateManager:
    """Generates and applies .env templates (stripped of values) from a vault."""

    PLACEHOLDER = "<value>"

    def __init__(self, vault: Vault):
        self.vault = vault

    def export_template(self, output_path: Path, key: str) -> int:
        """Decrypt vault and write a .env.example with values replaced by placeholders.

        Returns the number of keys written.
        """
        try:
            content = self.vault.unlock(key)
        except VaultError as exc:
            raise TemplateError(f"Failed to unlock vault: {exc}") from exc

        lines = []
        key_count = 0
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                lines.append(line)
            elif "=" in stripped:
                var_name = stripped.split("=", 1)[0]
                lines.append(f"{var_name}={self.PLACEHOLDER}")
                key_count += 1
            else:
                lines.append(line)

        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return key_count

    def check_missing(self, env_path: Path, key: str) -> list[str]:
        """Return a list of keys present in the vault but missing from *env_path*."""
        try:
            vault_content = self.vault.unlock(key)
        except VaultError as exc:
            raise TemplateError(f"Failed to unlock vault: {exc}") from exc

        vault_keys = self._parse_keys(vault_content)

        if not env_path.exists():
            return sorted(vault_keys)

        local_keys = self._parse_keys(env_path.read_text(encoding="utf-8"))
        return sorted(vault_keys - local_keys)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_keys(content: str) -> set[str]:
        keys: set[str] = set()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                keys.add(stripped.split("=", 1)[0].strip())
        return keys
