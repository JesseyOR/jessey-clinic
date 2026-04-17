import base64
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class DataEncryption:
    """
    Handle encryption/decryption of sensitive patient data.
    Uses Fernet symmetric encryption.
    """
    
    _cipher = None
    _key = None
    
    @classmethod
    def _get_cipher(cls):
        """Get or create Fernet cipher using app secret key as base."""
        if cls._cipher is None:
            secret = current_app.config.get('SECRET_KEY', 'default-secret-key')
            # Derive a 32-byte key from secret
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'jessey_clinic_salt_2026',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
            cls._cipher = Fernet(key)
        return cls._cipher
    
    @classmethod
    def encrypt(cls, plaintext):
        """Encrypt a string."""
        if plaintext is None:
            return None
        if not isinstance(plaintext, str):
            plaintext = str(plaintext)
        try:
            cipher = cls._get_cipher()
            encrypted = cipher.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    @classmethod
    def decrypt(cls, ciphertext):
        """Decrypt a string."""
        if ciphertext is None:
            return None
        try:
            cipher = cls._get_cipher()
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    @classmethod
    def encrypt_patient_data(cls, patient):
        """
        Encrypt sensitive patient fields (allergies, blood type).
        Returns dict with encrypted values.
        """
        encrypted = {}
        if patient.allergies:
            encrypted['allergies'] = cls.encrypt(patient.allergies)
        if patient.blood_type:
            encrypted['blood_type'] = cls.encrypt(patient.blood_type)
        return encrypted
    
    @classmethod
    def decrypt_patient_data(cls, encrypted_data):
        """Decrypt patient sensitive fields."""
        decrypted = {}
        if encrypted_data.get('allergies'):
            decrypted['allergies'] = cls.decrypt(encrypted_data['allergies'])
        if encrypted_data.get('blood_type'):
            decrypted['blood_type'] = cls.decrypt(encrypted_data['blood_type'])
        return decrypted
    
    @classmethod
    def hash_for_audit(cls, data):
        """Create a non-reversible hash for audit purposes."""
        if not data:
            return None
        return hashlib.sha256(f"{data}{current_app.config.get('SECRET_KEY', '')}".encode()).hexdigest()[:16]