"""Security-related utility functions for authentication and data encryption."""

import hashlib

from cryptography.fernet import Fernet


def hash_password(password: str) -> str:
    """Hash a password using SHA-256.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hexadecimal hash of the password.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using Fernet symmetric encryption.

    Args:
        data (bytes): Data to encrypt.
        key (bytes): Encryption key (use Fernet.generate_key()).

    Returns:
        bytes: Encrypted data.
    """
    f = Fernet(key)
    return f.encrypt(data)
