"""
Token Encryption Utility
Encrypts and decrypts OAuth tokens for secure storage
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TokenEncryption:
    """
    Handles encryption and decryption of OAuth tokens
    
    Uses Fernet (symmetric encryption) with a key derived from environment variable
    """
    
    def __init__(self):
        """Initialize encryption with key from environment"""
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize Fernet cipher with key from environment"""
        try:
            # Get encryption key from environment
            encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
            
            if not encryption_key:
                logger.warning(
                    "TOKEN_ENCRYPTION_KEY not set. Generating temporary key. "
                    "Set TOKEN_ENCRYPTION_KEY in production!"
                )
                # Generate a temporary key (NOT for production!)
                encryption_key = Fernet.generate_key().decode()
            
            # Derive a proper Fernet key if needed
            if len(encryption_key) < 32:
                # Use PBKDF2 to derive a proper key
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'github_scoring_salt',  # Static salt (use unique per deployment in production)
                    iterations=100000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            else:
                key = encryption_key.encode()
            
            self._fernet = Fernet(key)
            logger.info("Token encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise RuntimeError(f"Encryption initialization failed: {e}")
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an OAuth token
        
        Args:
            token: Plain text OAuth token
            
        Returns:
            Encrypted token (base64 encoded)
            
        Raises:
            ValueError: If token is empty
            RuntimeError: If encryption fails
        """
        if not token:
            raise ValueError("Token cannot be empty")
        
        try:
            # Encrypt the token
            encrypted = self._fernet.encrypt(token.encode())
            
            # Return as base64 string for storage
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise RuntimeError(f"Failed to encrypt token: {e}")
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt an OAuth token
        
        Args:
            encrypted_token: Encrypted token (base64 encoded)
            
        Returns:
            Plain text OAuth token
            
        Raises:
            ValueError: If encrypted_token is empty
            RuntimeError: If decryption fails
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be empty")
        
        try:
            # Decrypt the token
            decrypted = self._fernet.decrypt(encrypted_token.encode())
            
            # Return as string
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise RuntimeError(f"Failed to decrypt token: {e}")
    
    def is_encrypted(self, token: str) -> bool:
        """
        Check if a token appears to be encrypted
        
        Args:
            token: Token to check
            
        Returns:
            True if token appears encrypted, False otherwise
        """
        if not token:
            return False
        
        try:
            # Try to decrypt - if it works, it's encrypted
            self._fernet.decrypt(token.encode())
            return True
        except Exception:
            # If decryption fails, it's not encrypted (or corrupted)
            return False


# Global instance
_token_encryption = None


def get_token_encryption() -> TokenEncryption:
    """
    Get global token encryption instance
    
    Returns:
        TokenEncryption instance
    """
    global _token_encryption
    
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    
    return _token_encryption


# Convenience functions
def encrypt_token(token: str) -> str:
    """
    Encrypt an OAuth token
    
    Args:
        token: Plain text OAuth token
        
    Returns:
        Encrypted token
    """
    return get_token_encryption().encrypt_token(token)


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt an OAuth token
    
    Args:
        encrypted_token: Encrypted token
        
    Returns:
        Plain text OAuth token
    """
    return get_token_encryption().decrypt_token(encrypted_token)


def is_token_encrypted(token: str) -> bool:
    """
    Check if a token is encrypted
    
    Args:
        token: Token to check
        
    Returns:
        True if encrypted, False otherwise
    """
    return get_token_encryption().is_encrypted(token)
