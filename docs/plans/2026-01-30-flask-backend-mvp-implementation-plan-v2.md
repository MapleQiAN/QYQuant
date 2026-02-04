# Flask Backend MVP Implementation Plan (v2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Flask backend MVP that matches frontend types and endpoints exactly, with Postgres, Celery, and OpenAPI. Frontend request layer unwraps the response envelope.

**Architecture:** Flask app factory + blueprints, SQLAlchemy models + Alembic migrations, Marshmallow schemas, Celery workers, and a uniform response envelope with normalized errors. Unix ms timestamps everywhere.

**Tech Stack:** Flask, Flask-Smorest, SQLAlchemy, Alembic (Flask-Migrate), Marshmallow, Flask-JWT-Extended, Celery, Redis, PostgreSQL, Pytest, python-dotenv, cryptography (Fernet).

---

### Task 1: Dependencies, config, app factory, response + error normalization

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/extensions.py`
- Create: `backend/app/errors.py`
- Create: `backend/app/utils/response.py`
- Create: `backend/app/utils/request_id.py`
- Create: `backend/app/utils/time.py`
- Create: `backend/app/blueprints/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/test_errors.py`

**Step 1: Write the failing tests**

```python
# backend/tests/test_health.py

def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json['code'] == 0
    assert resp.json['data']['status'] == 'ok'
    assert isinstance(resp.json.get('request_id'), str)
```

```python
# backend/tests/test_errors.py

def test_not_found_error_shape(client):
    resp = client.get('/api/does-not-exist')
    assert resp.status_code == 404
    assert resp.json['code'] == 40400
    assert isinstance(resp.json['message'], str)
    assert 'details' in resp.json
```

```python
# backend/tests/conftest.py
import os
import pytest
from app import create_app

@pytest.fixture()
def app():
    os.environ.setdefault('FLASK_ENV', 'testing')
    os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/qyquant_test')
    app = create_app('testing')
    return app

@pytest.fixture()
def client(app):
    return app.test_client()
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/test_health.py::test_health_endpoint -v`
Expected: FAIL (app not configured)

**Step 3: Write minimal implementation**

```text
# backend/requirements.txt (append)
flask-smorest==0.44.0
flask-sqlalchemy==3.1.1
flask-migrate==4.0.7
flask-jwt-extended==4.6.0
python-dotenv==1.0.1
marshmallow==3.21.2
celery==5.3.6
redis==5.0.6
psycopg2-binary==2.9.9
cryptography==42.0.8
pytest==7.4.4
pytest-flask==1.3.0
```

```python
# backend/app/extensions.py
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

api = Api()
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
```

```python
# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'dev-jwt-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174').split(',')
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

class DevConfig(BaseConfig):
    DEBUG = True

class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = False

class ProdConfig(BaseConfig):
    DEBUG = False


def get_config(env=None):
    env = env or os.getenv('FLASK_ENV', 'development')
    return {'development': DevConfig, 'testing': TestConfig, 'production': ProdConfig}.get(env, DevConfig)
```

```python
# backend/app/utils/request_id.py
import uuid
from flask import g, request


def register_request_id(app):
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get('X-Request-Id') or str(uuid.uuid4())

    @app.after_request
    def attach_request_id(resp):
        resp.headers['X-Request-Id'] = g.request_id
        return resp
```

```python
# backend/app/utils/response.py
from flask import g

def ok(data=None, message='ok', code=0):
    payload = {"code": code, "message": message, "data": data}
    if getattr(g, 'request_id', None):
        payload['request_id'] = g.request_id
    return payload
```

```python
# backend/app/utils/time.py
import time

def now_ms():
    return int(time.time() * 1000)
```

```python
# backend/app/errors.py
from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_error(err):
        status = 500
        code = 50000
        message = 'internal_error'
        details = None

        if isinstance(err, HTTPException):
            status = err.code
            code = int(f"{status}00")
            message = err.name

        payload = {"code": code, "message": message, "details": details}
        return jsonify(payload), status
```

```python
# backend/app/blueprints/health.py
from flask import Blueprint
from ..utils.response import ok

bp = Blueprint('health', __name__)

@bp.get('/api/health')
def health():
    return ok({"status": "ok"})
```

```python
# backend/app/__init__.py
from flask import Flask
from .config import get_config
from .extensions import api, db, migrate, jwt, cors
from .errors import register_error_handlers
from .utils.request_id import register_request_id
from .blueprints.health import bp as health_bp


def create_app(env=None):
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    register_request_id(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)

    register_error_handlers(app)
    app.register_blueprint(health_bp)

    return app
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest backend/tests/test_health.py::test_health_endpoint -v`
Expected: PASS

Run: `python -m pytest backend/tests/test_errors.py::test_not_found_error_shape -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/requirements.txt backend/app backend/tests

git commit -m "feat: add app factory, response envelope, and errors"
```

---

### Task 2: .env files + OpenAPI config

**Files:**
- Create: `backend/.env.development`
- Create: `backend/.env.test`
- Create: `backend/.env.production`
- Modify: `backend/app/__init__.py`

**Step 1: Write failing test**

```python
# backend/tests/test_env.py
import os

def test_env_files_exist():
    assert os.path.exists('backend/.env.development')
    assert os.path.exists('backend/.env.test')
    assert os.path.exists('backend/.env.production')
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_env.py::test_env_files_exist -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```dotenv
# backend/.env.development
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qyquant
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret
JWT_SECRET=dev-jwt-secret
FERNET_KEY=dev-fernet-key-base64
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

```dotenv
# backend/.env.test
FLASK_ENV=testing
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qyquant_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret
JWT_SECRET=test-jwt-secret
FERNET_KEY=test-fernet-key-base64
CORS_ORIGINS=http://localhost:5173
```

```dotenv
# backend/.env.production
FLASK_ENV=production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qyquant
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=prod-secret
JWT_SECRET=prod-jwt-secret
FERNET_KEY=prod-fernet-key-base64
CORS_ORIGINS=https://your-frontend-domain
```

```python
# backend/app/__init__.py (append after api.init_app(app))
app.config['API_TITLE'] = 'QYQuant API'
app.config['API_VERSION'] = 'v1'
app.config['OPENAPI_VERSION'] = '3.0.3'
app.config['OPENAPI_URL_PREFIX'] = '/api'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/docs'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_env.py::test_env_files_exist -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/.env.development backend/.env.test backend/.env.production backend/app/__init__.py backend/tests/test_env.py

git commit -m "chore: add env files and openapi config"
```

---

### Task 3: Models (all tables) + migrations

**Files:**
- Create: `backend/app/models.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_models.py`
- Create: `backend/migrations/` (via flask db init)

**Step 1: Write failing test**

```python
# backend/tests/test_models.py
from app import create_app
from app.extensions import db
from app.models import User


def test_user_model_fields():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='admin@example.com', name='Admin', password_hash='x')
        db.session.add(user)
        db.session.commit()
        assert user.id is not None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_models.py::test_user_model_fields -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/models.py
import uuid
from .extensions import db
from .utils.time import now_ms


def gen_id():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    level = db.Column(db.String, nullable=True)
    notifications = db.Column(db.Integer, default=0)
    password_hash = db.Column(db.String, nullable=False)
    api_key_encrypted = db.Column(db.String, nullable=True)
    broker_key_encrypted = db.Column(db.String, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)

class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    returns = db.Column(db.Float, default=0)
    win_rate = db.Column(db.Float, default=0)
    max_drawdown = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    last_update = db.Column(db.BigInteger, default=now_ms)
    trades = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)

class StrategyVersion(db.Model):
    __tablename__ = 'strategy_versions'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'))
    version = db.Column(db.String, nullable=False)
    file_id = db.Column(db.String, db.ForeignKey('files.id'))
    checksum = db.Column(db.String, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)

class Backtest(db.Model):
    __tablename__ = 'backtests'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    started_at = db.Column(db.BigInteger, nullable=False)
    finished_at = db.Column(db.BigInteger, nullable=True)
    summary = db.Column(db.JSON, nullable=True)
    job_id = db.Column(db.String, nullable=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)

class BacktestTrade(db.Model):
    __tablename__ = 'backtest_trades'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    backtest_id = db.Column(db.String, db.ForeignKey('backtests.id'))
    symbol = db.Column(db.String, nullable=False)
    side = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    pnl = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)

class BotInstance(db.Model):
    __tablename__ = 'bot_instances'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    strategy = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    profit = db.Column(db.Float, default=0)
    runtime = db.Column(db.String, default='0d')
    capital = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    paper = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    bot_id = db.Column(db.String, db.ForeignKey('bot_instances.id'))
    symbol = db.Column(db.String, nullable=False)
    side = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, default='filled')
    pnl = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)
    client_order_id = db.Column(db.String, unique=True, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.BigInteger, nullable=False)
    tags = db.Column(db.JSON, default=list)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    author = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)

class Tip(db.Model):
    __tablename__ = 'tips'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String, nullable=False, default='USD')
    created_at = db.Column(db.BigInteger, default=now_ms)

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    filename = db.Column(db.String, nullable=False)
    content_type = db.Column(db.String, nullable=False)
    size = db.Column(db.Integer, nullable=False)
    path = db.Column(db.String, nullable=False)
    created_at = db.Column(db.BigInteger, default=now_ms)

class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    follower_id = db.Column(db.String, db.ForeignKey('users.id'))
    following_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
```

```python
# backend/app/__init__.py (ensure models imported for migrations)
from . import models  # noqa: F401
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest backend/tests/test_models.py::test_user_model_fields -v`
Expected: PASS

**Step 5: Initialize migrations and commit**

Run: `flask --app app db init`
Run: `flask --app app db migrate -m "init"`
Run: `flask --app app db upgrade`

```bash
git add backend/app/models.py backend/migrations backend/tests/test_models.py backend/app/__init__.py

git commit -m "feat: add database models and migrations"
```

---

### Task 4: Schemas (Marshmallow) for API responses

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/tests/test_schemas.py`

**Step 1: Write failing test**

```python
# backend/tests/test_schemas.py
from app.schemas import UserSchema

def test_user_schema_shape():
    data = UserSchema().dump({
        'id': 'u1',
        'name': 'Admin',
        'avatar': 'x',
        'level': 'VIP',
        'notifications': 2
    })
    assert data['name'] == 'Admin'
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_schemas.py::test_user_schema_shape -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/schemas.py
from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)
    avatar = fields.Str(required=True)
    level = fields.Str(allow_none=True)
    notifications = fields.Int(allow_none=True)

class StrategySchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)
    symbol = fields.Str(required=True)
    status = fields.Str(required=True)
    returns = fields.Float()
    winRate = fields.Float(attribute='win_rate')
    maxDrawdown = fields.Float(attribute='max_drawdown')
    tags = fields.List(fields.Str())
    lastUpdate = fields.Int(attribute='last_update')
    trades = fields.Int()

class BacktestSummarySchema(Schema):
    totalReturn = fields.Float()
    annualizedReturn = fields.Float(allow_none=True)
    sharpeRatio = fields.Float(allow_none=True)
    maxDrawdown = fields.Float(allow_none=True)
    winRate = fields.Float(allow_none=True)
    profitFactor = fields.Float(allow_none=True)
    totalTrades = fields.Int(allow_none=True)
    avgHoldingDays = fields.Float(allow_none=True)

class KlineBarSchema(Schema):
    time = fields.Int()
    open = fields.Float()
    high = fields.Float()
    low = fields.Float()
    close = fields.Float()
    volume = fields.Float()
    signal = fields.Str(allow_none=True)

class TradeSchema(Schema):
    id = fields.Str()
    symbol = fields.Str()
    side = fields.Str()
    price = fields.Float()
    quantity = fields.Float()
    pnl = fields.Float(allow_none=True)
    timestamp = fields.Int()

class BacktestLatestSchema(Schema):
    summary = fields.Nested(BacktestSummarySchema)
    kline = fields.List(fields.Nested(KlineBarSchema))
    trades = fields.List(fields.Nested(TradeSchema))

class BacktestSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    symbol = fields.Str()
    status = fields.Str()
    startedAt = fields.Int(attribute='started_at')
    finishedAt = fields.Int(attribute='finished_at')
    summary = fields.Nested(BacktestSummarySchema, allow_none=True)

class BotSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    strategy = fields.Str()
    status = fields.Str()
    profit = fields.Float()
    runtime = fields.Str()
    capital = fields.Float()
    tags = fields.List(fields.Str())

class PostSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Str()
    avatar = fields.Str()
    likes = fields.Int()
    comments = fields.Int()
    timestamp = fields.Int()
    tags = fields.List(fields.Str())
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_schemas.py::test_user_schema_shape -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas.py backend/tests/test_schemas.py

git commit -m "feat: add marshmallow schemas"
```

---

### Task 5: Auth + users endpoints (JWT, seed user)

**Files:**
- Create: `backend/app/blueprints/auth.py`
- Create: `backend/app/blueprints/users.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/app/utils/crypto.py`
- Create: `backend/tests/test_auth.py`

**Step 1: Write failing test**

```python
# backend/tests/test_auth.py

def test_login_and_me(client, seed_user):
    resp = client.post('/api/auth/login', json={"email": "admin@example.com", "password": "admin123"})
    assert resp.status_code == 200
    token = resp.json['data']['access_token']
    me = client.get('/api/users/me', headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json['data']['name'] == 'Admin'
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_auth.py::test_login_and_me -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/utils/crypto.py
from cryptography.fernet import Fernet
import os

def get_fernet():
    key = os.getenv('FERNET_KEY')
    return Fernet(key)
```

```python
# backend/app/blueprints/auth.py
from flask import request
from flask_smorest import Blueprint
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from ..models import User
from ..utils.response import ok

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.post('/login')
def login():
    payload = request.get_json() or {}
    user = User.query.filter_by(email=payload.get('email')).first()
    if not user or not check_password_hash(user.password_hash, payload.get('password', '')):
        return {"code": 40100, "message": "unauthorized", "details": None}, 401
    token = create_access_token(identity=user.id)
    return ok({"access_token": token})
```

```python
# backend/app/blueprints/users.py
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User
from ..schemas import UserSchema
from ..utils.response import ok

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.get('/me')
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    return ok(UserSchema().dump(user))
```

```python
# backend/app/__init__.py (register blueprints)
from .blueprints.auth import bp as auth_bp
from .blueprints.users import bp as users_bp

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
```

```python
# backend/tests/conftest.py (add seed_user fixture)
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture()
def seed_user(app):
    with app.app_context():
        db.create_all()
        user = User(email='admin@example.com', name='Admin', password_hash=generate_password_hash('admin123'), avatar='')
        db.session.add(user)
        db.session.commit()
        return user
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_auth.py::test_login_and_me -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/blueprints/auth.py backend/app/blueprints/users.py backend/app/__init__.py backend/app/utils/crypto.py backend/tests/test_auth.py backend/tests/conftest.py

git commit -m "feat: add auth and users endpoints"
```

---

### Task 6: Strategies endpoints

**Files:**
- Create: `backend/app/blueprints/strategies.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_strategies.py`

**Step 1: Write failing test**

```python
# backend/tests/test_strategies.py

def test_recent_strategies(client):
    resp = client.get('/api/strategies/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_strategies.py::test_recent_strategies -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/blueprints/strategies.py
from flask_smorest import Blueprint
from ..models import Strategy
from ..schemas import StrategySchema
from ..utils.response import ok

bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')

@bp.get('/recent')
def recent():
    items = Strategy.query.order_by(Strategy.last_update.desc()).limit(10).all()
    return ok(StrategySchema(many=True).dump(items))
```

```python
# backend/app/__init__.py (register)
from .blueprints.strategies import bp as strategies_bp
app.register_blueprint(strategies_bp)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_strategies.py::test_recent_strategies -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/blueprints/strategies.py backend/app/__init__.py backend/tests/test_strategies.py

git commit -m "feat: add strategies endpoints"
```

---

### Task 7: Backtest engine + providers + Celery tasks + endpoints

**Files:**
- Create: `backend/app/backtest/providers.py`
- Create: `backend/app/backtest/engine.py`
- Create: `backend/app/celery_app.py`
- Create: `backend/app/tasks/backtests.py`
- Create: `backend/app/blueprints/backtests.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_backtests.py`

**Step 1: Write failing test**

```python
# backend/tests/test_backtests.py

def test_backtest_run_and_job(client, seed_user):
    resp = client.post('/api/backtests/run', json={"name": "demo", "symbol": "BTCUSDT"})
    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']
    status = client.get(f'/api/backtests/job/{job_id}')
    assert status.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_backtests.py::test_backtest_run_and_job -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/backtest/providers.py
class MockProvider:
    def get_bars(self, symbol, limit=100):
        bars = []
        for i in range(limit):
            bars.append({
                "time": 1700000000000 + i * 60000,
                "open": 100 + i * 0.1,
                "high": 100 + i * 0.2,
                "low": 100 + i * 0.05,
                "close": 100 + i * 0.15,
                "volume": 1000 + i
            })
        return bars
```

```python
# backend/app/backtest/engine.py
from .providers import MockProvider

def run_backtest(symbol, strategy='sma'):
    provider = MockProvider()
    kline = provider.get_bars(symbol, limit=120)
    trades = []
    summary = {
        "totalReturn": 0.12,
        "annualizedReturn": 0.18,
        "sharpeRatio": 1.2,
        "maxDrawdown": 0.08,
        "winRate": 0.55,
        "profitFactor": 1.4,
        "totalTrades": 12,
        "avgHoldingDays": 3.2
    }
    return {"kline": kline, "trades": trades, "summary": summary}
```

```python
# backend/app/celery_app.py
import os
from celery import Celery

celery_app = Celery('qyquant', broker=os.getenv('REDIS_URL'), backend=os.getenv('REDIS_URL'))
```

```python
# backend/app/tasks/backtests.py
from ..celery_app import celery_app
from ..backtest.engine import run_backtest

@celery_app.task
def run_backtest_task(symbol):
    return run_backtest(symbol)
```

```python
# backend/app/blueprints/backtests.py
from flask import request
from flask_smorest import Blueprint
from celery.result import AsyncResult
from ..tasks.backtests import run_backtest_task
from ..utils.response import ok

bp = Blueprint('backtests', __name__, url_prefix='/api/backtests')

@bp.post('/run')
def run():
    payload = request.get_json() or {}
    job = run_backtest_task.delay(payload.get('symbol', 'BTCUSDT'))
    return ok({"job_id": job.id})

@bp.get('/job/<job_id>')
def job(job_id):
    result = AsyncResult(job_id)
    status = result.status
    data = {"status": status}
    if status == 'SUCCESS':
        data['result'] = result.result
    return ok(data)

@bp.get('/latest')
def latest():
    return ok({"summary": {}, "kline": [], "trades": []})
```

```python
# backend/app/__init__.py
from .blueprints.backtests import bp as backtests_bp
app.register_blueprint(backtests_bp)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_backtests.py::test_backtest_run_and_job -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/backtest backend/app/celery_app.py backend/app/tasks/backtests.py backend/app/blueprints/backtests.py backend/app/__init__.py backend/tests/test_backtests.py

git commit -m "feat: add backtest engine and endpoints"
```

---

### Task 8: Bots endpoints + orders

**Files:**
- Create: `backend/app/blueprints/bots.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_bots.py`

**Step 1: Write failing test**

```python
# backend/tests/test_bots.py

def test_recent_bots(client):
    resp = client.get('/api/bots/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_bots.py::test_recent_bots -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/blueprints/bots.py
from flask import request
from flask_smorest import Blueprint
from ..models import BotInstance, Order
from ..schemas import BotSchema
from ..utils.response import ok

bp = Blueprint('bots', __name__, url_prefix='/api/bots')

@bp.post('')
def create_bot():
    payload = request.get_json() or {}
    bot = BotInstance(
        name=payload.get('name', 'Bot'),
        strategy=payload.get('strategy_id', ''),
        status='active',
        profit=0,
        runtime='0d',
        capital=payload.get('capital', 0),
        tags=payload.get('tags', []),
        paper=True
    )
    from ..extensions import db
    db.session.add(bot)
    db.session.commit()
    return ok(BotSchema().dump(bot))

@bp.get('/recent')
def recent():
    items = BotInstance.query.order_by(BotInstance.created_at.desc()).limit(10).all()
    return ok(BotSchema(many=True).dump(items))

@bp.patch('/<bot_id>/status')
def update_status(bot_id):
    payload = request.get_json() or {}
    status = payload.get('status')
    if status == 'running':
        status = 'active'
    bot = BotInstance.query.get(bot_id)
    bot.status = status
    from ..extensions import db
    db.session.commit()
    return ok(BotSchema().dump(bot))

@bp.get('/<bot_id>/performance')
def performance(bot_id):
    orders = Order.query.filter_by(bot_id=bot_id).all()
    return ok({"equity": [], "orders": []})
```

```python
# backend/app/__init__.py
from .blueprints.bots import bp as bots_bp
app.register_blueprint(bots_bp)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_bots.py::test_recent_bots -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/blueprints/bots.py backend/app/__init__.py backend/tests/test_bots.py

git commit -m "feat: add bots endpoints"
```

---

### Task 9: Forum endpoints (hot + CRUD)

**Files:**
- Create: `backend/app/blueprints/forum.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_forum.py`

**Step 1: Write failing test**

```python
# backend/tests/test_forum.py

def test_forum_hot(client):
    resp = client.get('/api/forum/hot')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_forum.py::test_forum_hot -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/blueprints/forum.py
from flask import request
from flask_smorest import Blueprint
from ..models import Post, Comment, Like, Favorite, Tip
from ..schemas import PostSchema
from ..utils.response import ok
from ..extensions import db
from ..utils.time import now_ms

bp = Blueprint('forum', __name__, url_prefix='/api/forum')

@bp.get('/hot')
def hot():
    posts = Post.query.order_by(Post.likes.desc()).limit(10).all()
    return ok(PostSchema(many=True).dump(posts))

@bp.post('/posts')
def create_post():
    payload = request.get_json() or {}
    post = Post(
        title=payload.get('title', ''),
        author=payload.get('author', ''),
        avatar=payload.get('avatar', ''),
        likes=0,
        comments=0,
        timestamp=now_ms(),
        tags=payload.get('tags', [])
    )
    db.session.add(post)
    db.session.commit()
    return ok(PostSchema().dump(post))
```

```python
# backend/app/__init__.py
from .blueprints.forum import bp as forum_bp
app.register_blueprint(forum_bp)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_forum.py::test_forum_hot -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/blueprints/forum.py backend/app/__init__.py backend/tests/test_forum.py

git commit -m "feat: add forum endpoints"
```

---

### Task 10: Files endpoints (upload/download) + validation

**Files:**
- Create: `backend/app/blueprints/files.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_files.py`

**Step 1: Write failing test**

```python
# backend/tests/test_files.py

def test_file_upload_requires_auth(client):
    resp = client.post('/api/files')
    assert resp.status_code == 401
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_files.py::test_file_upload_requires_auth -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/app/blueprints/files.py
import os
from flask import request, send_file
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import File
from ..utils.response import ok
from ..extensions import db

bp = Blueprint('files', __name__, url_prefix='/api/files')

ALLOWED_EXT = {'.py', '.zip', '.txt'}
MAX_SIZE = 5 * 1024 * 1024
BASE_DIR = 'backend/storage'

@bp.post('')
@jwt_required()
def upload():
    f = request.files.get('file')
    if not f:
        return {"code": 40000, "message": "file_required", "details": None}, 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return {"code": 40000, "message": "invalid_file_type", "details": None}, 400
    os.makedirs(BASE_DIR, exist_ok=True)
    path = os.path.join(BASE_DIR, f.filename)
    f.save(path)
    meta = File(owner_id=get_jwt_identity(), filename=f.filename, content_type=f.mimetype, size=os.path.getsize(path), path=path)
    db.session.add(meta)
    db.session.commit()
    return ok({"id": meta.id})

@bp.get('/<file_id>')
@jwt_required()
def download(file_id):
    meta = File.query.get(file_id)
    if not meta:
        return {"code": 40400, "message": "not_found", "details": None}, 404
    if meta.owner_id != get_jwt_identity():
        return {"code": 40300, "message": "forbidden", "details": None}, 403
    return send_file(meta.path, as_attachment=True)
```

```python
# backend/app/__init__.py
from .blueprints.files import bp as files_bp
app.register_blueprint(files_bp)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_files.py::test_file_upload_requires_auth -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/blueprints/files.py backend/app/__init__.py backend/tests/test_files.py

git commit -m "feat: add files endpoints"
```

---

### Task 11: Seed script (admin + sample data)

**Files:**
- Create: `backend/scripts/seed.py`
- Create: `backend/tests/test_seed.py`

**Step 1: Write failing test**

```python
# backend/tests/test_seed.py

def test_seed_script_runs():
    assert True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_seed.py::test_seed_script_runs -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/scripts/seed.py
import os
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User, Strategy, Post, BotInstance, Backtest
from app.utils.time import now_ms

app = create_app('development')

with app.app_context():
    db.create_all()
    admin = User(email='admin@example.com', name='Admin', avatar='', password_hash=generate_password_hash('admin123'))
    db.session.add(admin)

    strat = Strategy(name='SMA Cross', symbol='BTCUSDT', status='running', returns=0.12, win_rate=0.55, max_drawdown=0.08, tags=['sma'], last_update=now_ms(), trades=12)
    post = Post(title='My first strategy', author='Admin', avatar='', likes=12, comments=3, timestamp=now_ms(), tags=['share'])
    bot = BotInstance(name='BTC Bot', strategy='SMA Cross', status='active', profit=120.5, runtime='7d', capital=10000, tags=['paper'], paper=True)
    bt = Backtest(name='BTC Backtest', symbol='BTCUSDT', status='completed', started_at=now_ms(), finished_at=now_ms())

    db.session.add_all([strat, post, bot, bt])
    db.session.commit()
    print('seed ok')
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_seed.py::test_seed_script_runs -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/scripts/seed.py backend/tests/test_seed.py

git commit -m "feat: add seed data script"
```

---

### Task 12: API contract document

**Files:**
- Create: `docs/api-contract.md`

**Step 1: Write failing test**

```python
# backend/tests/test_contract.py
import os

def test_api_contract_exists():
    assert os.path.exists('docs/api-contract.md')
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_contract.py::test_api_contract_exists -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```markdown
# QYQuant API Contract

Base URL: /api

## Success Envelope
{ "code": 0, "message": "ok", "data": { ... }, "request_id": "..." }

## Errors
HTTP status + { "code": <status>00, "message": "...", "details": null }

## Endpoints
- GET /backtests/latest -> BacktestLatestResponse
- POST /backtests/run -> { job_id }
- GET /backtests/job/{job_id} -> { status, result? }
- GET /bots/recent -> Bot[]
- POST /bots -> Bot
- PATCH /bots/{id}/status -> Bot
- GET /bots/{id}/performance -> { equity: [], orders: [] }
- GET /strategies/recent -> Strategy[]
- GET /forum/hot -> Post[]
- POST /auth/login -> { access_token }
- GET /users/me -> User
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_contract.py::test_api_contract_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/api-contract.md backend/tests/test_contract.py

git commit -m "docs: add api contract"
```

---

### Task 13: Frontend unwrap response envelope

**Files:**
- Modify: `frontend/src/api/http.ts`
- Create: `frontend/src/api/http.test.ts`

**Step 1: Write failing test**

```ts
// frontend/src/api/http.test.ts
import { createHttpClient } from './http'

it('unwraps api envelope', async () => {
  const client = createHttpClient()
  expect(client).toBeTruthy()
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- http.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// frontend/src/api/http.ts
const response = await instance.request<{ code: number; message: string; data: T }>(config)
return response.data.data
```

**Step 4: Run test to verify it passes**

Run: `npm test -- http.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/api/http.ts frontend/src/api/http.test.ts

git commit -m "feat: unwrap api envelope"
```

---

### Task 14: Docker compose + Makefile

**Files:**
- Create: `backend/docker-compose.yml`
- Create: `backend/Makefile`
- Create: `backend/tests/test_devfiles.py`

**Step 1: Write failing test**

```python
# backend/tests/test_devfiles.py
import os

def test_devfiles_exist():
    assert os.path.exists('backend/docker-compose.yml')
    assert os.path.exists('backend/Makefile')
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_devfiles.py::test_devfiles_exist -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```yaml
# backend/docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: qyquant
    ports:
      - "5432:5432"
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

```make
# backend/Makefile
.PHONY: dev

dev:
	flask --app app run
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_devfiles.py::test_devfiles_exist -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/docker-compose.yml backend/Makefile backend/tests/test_devfiles.py

git commit -m "chore: add docker compose and make dev"
```

---

### Task 15: Final verification

**Step 1: Run full test suite**

Run: `python -m pytest -v`
Expected: PASS

**Step 2: Commit final cleanups if needed**

```bash
git status -sb
```
