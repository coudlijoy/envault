"""Sync module for sharing encrypted vault files across team members."""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional

from envault.vault import Vault, VaultError


class SyncError(Exception):
    """Raised when a sync operation fails."""
    pass


class SyncManager:
    """Manages syncing of encrypted vault files to/from a shared location."""

    VAULT_FILENAME = ".env.vault"

    def __init__(self, shared_dir: str, vault: Vault):
        """
        Initialize the SyncManager.

        Args:
            shared_dir: Path to the shared directory (e.g., a mounted drive or repo folder).
            vault: An initialized Vault instance.
        """
        self.shared_dir = Path(shared_dir)
        self.vault = vault

    def _shared_vault_path(self) -> Path:
        return self.shared_dir / self.VAULT_FILENAME

    def _checksum(self, path: Path) -> str:
        """Compute MD5 checksum of a file."""
        h = hashlib.md5()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    def push(self, env_file: str, key: str) -> str:
        """
        Encrypt the local .env file and push it to the shared directory.

        Returns the path of the pushed vault file.
        """
        if not self.shared_dir.exists():
            raise SyncError(f"Shared directory does not exist: {self.shared_dir}")

        vault_file = self.vault.lock(env_file, key)
        dest = self._shared_vault_path()
        shutil.copy2(vault_file, dest)
        return str(dest)

    def pull(self, key: str, output_file: Optional[str] = None) -> str:
        """
        Pull the encrypted vault from the shared directory and decrypt it.

        Returns the path of the decrypted .env file.
        """
        src = self._shared_vault_path()
        if not src.exists():
            raise SyncError(f"No vault file found in shared directory: {self.shared_dir}")

        local_vault = Path(self.vault.vault_path)
        shutil.copy2(src, local_vault)
        return self.vault.unlock(str(local_vault), key, output_file)

    def is_outdated(self) -> bool:
        """
        Check if the local vault differs from the shared vault.

        Returns True if local vault is missing or differs from shared.
        """
        shared = self._shared_vault_path()
        local = Path(self.vault.vault_path)

        if not shared.exists():
            return False
        if not local.exists():
            return True
        return self._checksum(shared) != self._checksum(local)
