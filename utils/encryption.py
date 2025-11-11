"""
Encryption utilities for HIPAA-compliant data protection.
Uses Fernet (symmetric encryption) for encrypting PHI at rest.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.

    HIPAA Compliance: §164.312(a)(2)(iv) - Encryption and Decryption
    Uses Fernet (AES-128 in CBC mode with HMAC for authentication).
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager with a key.

        Args:
            encryption_key: Base64-encoded Fernet key from environment variable
        """
        # Get encryption key from environment or use provided key
        key = encryption_key or os.getenv('ENCRYPTION_KEY')

        if not key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if plaintext is None or plaintext == '':
            return plaintext

        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: The encrypted string to decrypt

        Returns:
            Decrypted plaintext string
        """
        if ciphertext is None or ciphertext == '':
            return ciphertext

        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file on disk.

        Args:
            file_path: Path to file to encrypt
            output_path: Optional output path (defaults to file_path + '.encrypted')

        Returns:
            Path to encrypted file
        """
        output_path = output_path or f"{file_path}.encrypted"

        with open(file_path, 'rb') as f:
            plaintext = f.read()

        encrypted = self.cipher.encrypt(plaintext)

        with open(output_path, 'wb') as f:
            f.write(encrypted)

        return output_path

    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file on disk.

        Args:
            file_path: Path to encrypted file
            output_path: Optional output path (defaults to file_path without '.encrypted')

        Returns:
            Path to decrypted file
        """
        if not output_path:
            output_path = file_path.replace('.encrypted', '') if file_path.endswith('.encrypted') else f"{file_path}.decrypted"

        with open(file_path, 'rb') as f:
            encrypted = f.read()

        decrypted = self.cipher.decrypt(encrypted)

        with open(output_path, 'wb') as f:
            f.write(decrypted)

        return output_path


def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Generate a Fernet key from a password using PBKDF2.

    Args:
        password: Master password
        salt: Salt for key derivation (should be stored)

    Returns:
        Base64-encoded Fernet key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommendation for 2024
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def generate_new_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded Fernet key as string
    """
    return Fernet.generate_key().decode()


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance.

    Returns:
        EncryptionManager singleton instance
    """
    global _encryption_manager

    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()

    return _encryption_manager


# Convenience functions for simple encryption/decryption
def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value."""
    return get_encryption_manager().encrypt(plaintext)


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a string value."""
    return get_encryption_manager().decrypt(ciphertext)


if __name__ == '__main__':
    # Generate a new encryption key
    print("Generate a new encryption key and add it to your .env file:")
    print(f"ENCRYPTION_KEY={generate_new_key()}")
