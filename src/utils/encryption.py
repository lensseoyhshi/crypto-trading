"""
Encryption utilities for sensitive data
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

from ..core.config import get_settings


class EncryptionManager:
    """Manager for encrypting/decrypting sensitive data"""
    
    def __init__(self, password: str = None):
        if not password:
            settings = get_settings()
            password = settings.security.secret_key
        
        self._key = self._derive_key(password)
        self._fernet = Fernet(self._key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        try:
            # Use a fixed salt for consistency (in production, consider using unique salts)
            salt = b'crypto_trading_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key
        except Exception as e:
            logger.error(f"Failed to derive encryption key: {e}")
            raise
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()


# Global encryption manager instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
