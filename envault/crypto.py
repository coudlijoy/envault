"""Encryption and decryption utilities for envault using AES-GCM via Fernet."""

import os
import base64
import secrets
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
ITERATIONS = 390000


def generate_key() -> str:
    """Generate a new random Fernet key encoded as a URL-safe base64 string."""
    return Fernet.generate_key().decode()


def derive_key(passphrase: str, salt: bytes | None = None) -> tuple[str, bytes]:
    """Derive a Fernet-compatible key from a passphrase using PBKDF2-HMAC-SHA256.

    Returns:
        A tuple of (base64-encoded key string, salt bytes).
    """
    if salt is None:
        salt = secrets.token_bytes(SALT_SIZE)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key_bytes.decode(), salt


def encrypt(plaintext: str, key: str) -> bytes:
    """Encrypt a plaintext string using the provided Fernet key.

    Args:
        plaintext: The string content to encrypt.
        key: A Fernet-compatible key string.

    Returns:
        Encrypted bytes (Fernet token).
    """
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(plaintext.encode())


def decrypt(token: bytes, key: str) -> str:
    """Decrypt a Fernet token using the provided key.

    Args:
        token: Encrypted bytes (Fernet token).
        key: A Fernet-compatible key string.

    Returns:
        Decrypted plaintext string.

    Raises:
        ValueError: If the key is invalid or the token is corrupted.
    """
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(token).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid key or corrupted data.") from exc
