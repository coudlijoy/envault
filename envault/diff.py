"""Diff module for comparing .env file versions stored in the vault."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envault.vault import Vault, VaultError


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffResult:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    modified: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def summary(self) -> str:
        lines = []
        for key, val in self.added.items():
            lines.append(f"+ {key}={val}")
        for key, val in self.removed.items():
            lines.append(f"- {key}={val}")
        for key, (old, new) in self.modified.items():
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "No changes."


def _parse_env(content: str) -> Dict[str, str]:
    """Parse .env content into a key/value dict, ignoring comments and blanks."""
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


class VaultDiff:
    """Compare decrypted vault contents against a local .env file."""

    def __init__(self, vault: Vault, shared_key: str):
        self.vault = vault
        self.shared_key = shared_key

    def diff_with_file(self, env_path: Path) -> DiffResult:
        """Return a DiffResult comparing the vault to the given .env file."""
        try:
            vault_content = self.vault.unlock(self.shared_key)
        except VaultError as exc:
            raise DiffError(f"Failed to unlock vault: {exc}") from exc

        if not env_path.exists():
            raise DiffError(f"File not found: {env_path}")

        local_content = env_path.read_text(encoding="utf-8")
        vault_vars = _parse_env(vault_content)
        local_vars = _parse_env(local_content)

        result = DiffResult()
        all_keys = set(vault_vars) | set(local_vars)

        for key in all_keys:
            in_vault = key in vault_vars
            in_local = key in local_vars
            if in_vault and not in_local:
                result.removed[key] = vault_vars[key]
            elif in_local and not in_vault:
                result.added[key] = local_vars[key]
            elif vault_vars[key] != local_vars[key]:
                result.modified[key] = (vault_vars[key], local_vars[key])

        return result
