import os

import pytest


def test_encrypt_decrypt_strategy_round_trip(monkeypatch):
    monkeypatch.setenv('STRATEGY_ENCRYPT_KEY', 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=')

    from app.utils.crypto import decrypt_strategy, encrypt_strategy

    plaintext = b'class Strategy:\n    pass\n'

    encrypted = encrypt_strategy(plaintext)

    assert encrypted != plaintext
    assert decrypt_strategy(encrypted) == plaintext


def test_encrypt_strategy_rejects_invalid_key(monkeypatch):
    monkeypatch.setenv('STRATEGY_ENCRYPT_KEY', 'invalid-key')

    from app.utils.crypto import encrypt_strategy

    with pytest.raises(ValueError):
        encrypt_strategy(b'print("hello")')
