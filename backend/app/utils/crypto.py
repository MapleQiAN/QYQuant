import os

from cryptography.fernet import Fernet


def get_fernet():
    key = os.getenv('FERNET_KEY')
    if not key:
        raise RuntimeError('FERNET_KEY is not set')
    return Fernet(key)


def encrypt_text(value):
    if value is None:
        return None
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_text(value):
    if value is None:
        return None
    return get_fernet().decrypt(value.encode()).decode()
