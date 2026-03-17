import base64
import binascii
import hashlib
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


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


def _get_strategy_encrypt_key():
    raw_value = os.getenv('STRATEGY_ENCRYPT_KEY')
    if not raw_value:
        raise RuntimeError('STRATEGY_ENCRYPT_KEY is not set')

    try:
        key = base64.b64decode(raw_value, validate=True)
    except binascii.Error as exc:
        raise ValueError('STRATEGY_ENCRYPT_KEY must be a base64-encoded 32-byte key') from exc

    if len(key) != 32:
        raise ValueError('STRATEGY_ENCRYPT_KEY must decode to 32 bytes')

    return key


def encrypt_strategy(plaintext):
    if plaintext is None:
        return None

    payload = plaintext if isinstance(plaintext, bytes) else str(plaintext).encode('utf-8')
    aesgcm = AESGCM(_get_strategy_encrypt_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    return nonce + ciphertext


def decrypt_strategy(payload):
    if payload is None:
        return None

    encrypted = payload if isinstance(payload, bytes) else bytes(payload)
    if len(encrypted) < 13:
        raise ValueError('Encrypted strategy payload is invalid')

    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    aesgcm = AESGCM(_get_strategy_encrypt_key())
    return aesgcm.decrypt(nonce, ciphertext, None)


def hash_strategy_source(source):
    payload = source if isinstance(source, bytes) else str(source).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()
