"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import generate_key, derive_key, encrypt, decrypt


class TestGenerateKey:
    def test_returns_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_key_is_unique(self):
        assert generate_key() != generate_key()

    def test_key_length(self):
        # Fernet keys are 44 base64 characters
        assert len(generate_key()) == 44


class TestDeriveKey:
    def test_returns_tuple(self):
        result = derive_key("my-passphrase")
        assert isinstance(result, tuple) and len(result) == 2

    def test_deterministic_with_same_salt(self):
        key1, salt = derive_key("secret")
        key2, _ = derive_key("secret", salt=salt)
        assert key1 == key2

    def test_different_passphrases_differ(self):
        key1, salt = derive_key("passphrase-one")
        key2, _ = derive_key("passphrase-two", salt=salt)
        assert key1 != key2

    def test_random_salt_generated(self):
        _, salt1 = derive_key("test")
        _, salt2 = derive_key("test")
        assert salt1 != salt2


class TestEncryptDecrypt:
    def test_roundtrip(self):
        key = generate_key()
        plaintext = "DATABASE_URL=postgres://localhost/mydb"
        token = encrypt(plaintext, key)
        assert decrypt(token, key) == plaintext

    def test_encrypt_returns_bytes(self):
        key = generate_key()
        token = encrypt("SECRET=abc", key)
        assert isinstance(token, bytes)

    def test_ciphertext_differs_from_plaintext(self):
        key = generate_key()
        plaintext = "API_KEY=12345"
        token = encrypt(plaintext, key)
        assert plaintext.encode() not in token

    def test_wrong_key_raises(self):
        key1 = generate_key()
        key2 = generate_key()
        token = encrypt("SECRET=value", key1)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, key2)

    def test_multiline_env_roundtrip(self):
        key = generate_key()
        content = "DB_HOST=localhost\nDB_PORT=5432\nAPI_SECRET=supersecret\n"
        assert decrypt(encrypt(content, key), key) == content
