"""Vault module for reading, writing, and managing encrypted .env vault files."""

import json
import os
from pathlib import Path
from typing import Optional

from envault.crypto import derive_key, encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"
DEFAULT_ENV_FILE = ".env"


class VaultError(Exception):
    """Raised when a vault operation fails."""
    pass


class Vault:
    """Manages an encrypted vault file that stores .env contents.

    The vault file is a JSON structure containing:
    - 'salt': hex-encoded salt used for key derivation
    - 'ciphertext': hex-encoded encrypted .env contents
    """

    def __init__(
        self,
        vault_path: str = DEFAULT_VAULT_FILE,
        env_path: str = DEFAULT_ENV_FILE,
    ):
        self.vault_path = Path(vault_path)
        self.env_path = Path(env_path)

    def lock(self, passphrase: str) -> None:
        """Encrypt the .env file and write it to the vault file.

        Args:
            passphrase: The shared passphrase used to derive the encryption key.

        Raises:
            VaultError: If the .env file does not exist or encryption fails.
        """
        if not self.env_path.exists():
            raise VaultError(
                f"Environment file not found: {self.env_path}"
            )

        plaintext = self.env_path.read_bytes()

        # Derive a key from the passphrase (generates a fresh random salt)
        key, salt = derive_key(passphrase)
        ciphertext = encrypt(key, plaintext)

        vault_data = {
            "salt": salt.hex(),
            "ciphertext": ciphertext.hex(),
        }

        self.vault_path.write_text(
            json.dumps(vault_data, indent=2), encoding="utf-8"
        )

    def unlock(self, passphrase: str, overwrite: bool = False) -> None:
        """Decrypt the vault file and write the contents to the .env file.

        Args:
            passphrase: The shared passphrase used to derive the decryption key.
            overwrite: If True, overwrite an existing .env file without error.

        Raises:
            VaultError: If the vault file is missing, malformed, or decryption fails.
        """
        if not self.vault_path.exists():
            raise VaultError(
                f"Vault file not found: {self.vault_path}"
            )

        if self.env_path.exists() and not overwrite:
            raise VaultError(
                f"{self.env_path} already exists. "
                "Pass overwrite=True to replace it."
            )

        try:
            vault_data = json.loads(self.vault_path.read_text(encoding="utf-8"))
            salt = bytes.fromhex(vault_data["salt"])
            ciphertext = bytes.fromhex(vault_data["ciphertext"])
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise VaultError(f"Vault file is malformed: {exc}") from exc

        # Re-derive the key using the stored salt
        key, _ = derive_key(passphrase, salt=salt)

        try:
            plaintext = decrypt(key, ciphertext)
        except Exception as exc:
            raise VaultError(
                "Decryption failed — wrong passphrase or corrupted vault."
            ) from exc

        self.env_path.write_bytes(plaintext)

    def is_locked(self) -> bool:
        """Return True if a vault file exists at the configured path."""
        return self.vault_path.exists()

    def status(self) -> dict:
        """Return a dict summarising the current vault and env file state."""
        return {
            "vault_file": str(self.vault_path),
            "env_file": str(self.env_path),
            "vault_exists": self.vault_path.exists(),
            "env_exists": self.env_path.exists(),
        }
