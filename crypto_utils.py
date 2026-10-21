import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.environ.get("POPIA_FERNET_KEY") or os.environ.get("FIELD_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("POPIA_FERNET_KEY not set in Render Environment")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def protect_id(national_id: str) -> str:
    encrypted_bytes = cipher_suite.encrypt(national_id.encode())
    return encrypted_bytes.decode()

def reveal_id(encrypted_id: str) -> str:
    decrypted_bytes = cipher_suite.decrypt(encrypted_id.encode())
    return decrypted_bytes.decode()
