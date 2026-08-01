import hashlib
import os

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

def hash_password(password: str) -> str:
    """Hash a password using standard library PBKDF2-HMAC-SHA256 (Python 3.13 compatible)."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its stored salt and PBKDF2 hash."""
    try:
        if ":" not in hashed_password:
            # Fallback for plain text comparison if legacy
            return plain_password == hashed_password
        salt_hex, hash_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return pwd_hash == expected_hash
    except Exception:
        return False

def verify_admin(email: str, password: str) -> bool:
    """Validate default admin credentials."""
    return email.strip().lower() == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD
