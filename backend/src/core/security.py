"""Security utilities for encryption and token management."""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from src.core.config import settings


def get_encryption_key() -> bytes:
    """Generate encryption key from settings."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"bridgeai_salt",
        iterations=100000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(
        kdf.derive(settings.ENCRYPTION_KEY.encode()))
    return key


def encrypt_token(token: str) -> str:
    """Encrypt a token for storage."""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(token.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token."""
    f = Fernet(get_encryption_key())
    decoded = base64.urlsafe_b64decode(encrypted_token.encode())
    decrypted = f.decrypt(decoded)
    return decrypted.decode()
