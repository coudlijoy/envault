"""Key rotation support for envault vaults."""

import os
import json
from datetime import datetime
from pathlib import Path
from envault.crypto import generate_key, encrypt, decrypt
from envault.vault import Vault, VaultError


class RotationError(Exception):
    """Raised when key rotation fails."""


class KeyRotator:
    """Handles rotating the encryption key for a vault."""

    ROTATION_LOG = ".envault_rotation_log.json"

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.rotation_log = self.vault_path.parent / self.ROTATION_LOG

    def rotate(self, current_key: str, new_key: str | None = None) -> str:
        """Rotate the encryption key. Returns the new key."""
        if not self.vault_path.exists():
            raise RotationError(f"Vault not found: {self.vault_path}")

        if new_key is None:
            new_key = generate_key()

        try:
            vault = Vault(str(self.vault_path), current_key)
            plaintext = vault.unlock()
        except VaultError as e:
            raise RotationError(f"Failed to unlock vault with current key: {e}") from e

        try:
            new_vault = Vault(str(self.vault_path), new_key)
            new_vault.lock(plaintext)
        except VaultError as e:
            raise RotationError(f"Failed to re-encrypt vault with new key: {e}") from e

        self._record_rotation()
        return new_key

    def _record_rotation(self):
        """Append a rotation event to the rotation log."""
        log = []
        if self.rotation_log.exists():
            try:
                with open(self.rotation_log, "r") as f:
                    log = json.load(f)
            except (json.JSONDecodeError, OSError):
                log = []

        log.append({"rotated_at": datetime.utcnow().isoformat(), "vault": str(self.vault_path)})

        with open(self.rotation_log, "w") as f:
            json.dump(log, f, indent=2)

    def rotation_history(self) -> list:
        """Return the list of recorded rotation events."""
        if not self.rotation_log.exists():
            return []
        try:
            with open(self.rotation_log, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
