import os
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash


os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', '1')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/1')

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
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/1')

    from app import create_app
    from app.extensions import db

    app = create_app('testing')
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seed_user(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = User(
            email='admin@example.com',
            name='Admin',
            password_hash=generate_password_hash('admin123'),
            avatar='',
        )
        db.session.add(user)
        db.session.commit()
        return user
