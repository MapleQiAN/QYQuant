import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', '1')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/1')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
os.environ.setdefault('STRATEGY_ENCRYPT_KEY', 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=')
os.environ.setdefault('E2B_API_KEY', 'test-e2b-api-key')

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _ensure_postgres_database(database_url):
    target_url = make_url(database_url)
    database_name = target_url.database
    if not database_name:
        return

    admin_database = "postgres" if database_name != "postgres" else "template1"
    admin_url = target_url.set(database=admin_database)
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        engine.dispose()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.db'
    storage_root = tmp_path / 'storage'
    postgres_test_url = os.getenv('QYQUANT_TEST_DATABASE_URL')
    monkeypatch.setenv('FLASK_ENV', 'testing')
    if postgres_test_url:
        _ensure_postgres_database(postgres_test_url)
        monkeypatch.setenv('DATABASE_URL', postgres_test_url)
    else:
        monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv('FERNET_KEY', 'fVFLNI0cSfGIaULo353R6ivdsuEVw7xdl5Hknr0bHFU=')
    monkeypatch.setenv('CELERY_TASK_ALWAYS_EAGER', '1')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
    monkeypatch.setenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    monkeypatch.setenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    monkeypatch.setenv('JWT_SECRET', 'test-jwt-secret-key-with-sufficient-length-123456')
    monkeypatch.setenv('AUTH_FIXED_SMS_CODE', '123456')
    monkeypatch.setenv('BACKTEST_DATA_PROVIDER', 'mock')
    monkeypatch.setenv('BACKTEST_STORAGE_DIR', storage_root.as_posix())
    monkeypatch.setenv('STRATEGY_STORAGE_DIR', storage_root.as_posix())
    monkeypatch.setenv('STRATEGY_ENCRYPT_KEY', 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=')
    monkeypatch.setenv('E2B_API_KEY', 'test-e2b-api-key')

    from app import create_app
    from app.extensions import db

    monkeypatch.setenv('BACKTEST_DATA_PROVIDER', 'mock')
    app = create_app('testing')
    with app.app_context():
        if postgres_test_url:
            db.session.execute(db.text('DROP SCHEMA IF EXISTS public CASCADE'))
            db.session.execute(db.text('CREATE SCHEMA public'))
            db.session.commit()
        db.create_all()
        if postgres_test_url:
            db.session.execute(db.text('CREATE EXTENSION IF NOT EXISTS zhparser'))
            db.session.execute(db.text('DROP TEXT SEARCH CONFIGURATION IF EXISTS chinese CASCADE'))
            db.session.execute(db.text('CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser)'))
            db.session.execute(
                db.text(
                    "ALTER TEXT SEARCH CONFIGURATION chinese "
                    "ADD MAPPING FOR n,v,a,i,e,l WITH simple"
                )
            )
            db.session.commit()
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
