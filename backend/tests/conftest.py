import os
import sys
from pathlib import Path

import pytest


os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', '1')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/1')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv('FERNET_KEY', 'fVFLNI0cSfGIaULo353R6ivdsuEVw7xdl5Hknr0bHFU=')
    monkeypatch.setenv('CELERY_TASK_ALWAYS_EAGER', '1')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
    monkeypatch.setenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    monkeypatch.setenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    monkeypatch.setenv('JWT_SECRET', 'test-jwt-secret-key-with-sufficient-length-123456')
    monkeypatch.setenv('AUTH_FIXED_SMS_CODE', '123456')
    monkeypatch.setenv('BACKTEST_DATA_PROVIDER', 'mock')

    from app import create_app
    from app.extensions import db

    monkeypatch.setenv('BACKTEST_DATA_PROVIDER', 'mock')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_auth_state():
    from app.utils.redis_client import reset_auth_store
    from app.utils.sms import reset_sms_sender

    reset_auth_store()
    reset_sms_sender()


@pytest.fixture()
def seed_user(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = User(
            phone='13800000000',
            nickname='Admin',
        )
        db.session.add(user)
        db.session.commit()
        return user
