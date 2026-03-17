
import hashlib
import io
import json
import uuid
import zipfile
from pathlib import Path

from app.extensions import db
from app.models import BacktestJob, File, Strategy, StrategyVersion


def _seed_runtime_strategy(app, tmp_path, *, owner_id=None, parameters=None):
    strategy_id = str(uuid.uuid4())
    version = '1.2.3'
    package_path = tmp_path / 'runtime-test.qys'
    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": "Runtime Descriptor Strategy",
        "version": version,
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
        "parameters": parameters
        or [
            {"key": "window", "type": "integer", "default": 20, "min": 1, "max": 200},
            {"key": "enabled", "type": "boolean", "default": True},
        ],
    }
    source = """
class Strategy:
    def on_bar(self, ctx, bar):
        return None
"""
    with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('strategy.json', json.dumps(manifest))
        archive.writestr('src/strategy.py', source)

    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            name='Runtime Descriptor Strategy',
            symbol='BTCUSDT',
            status='draft',
            owner_id=owner_id,
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=['runtime'],
            trades=0,
        )
        db.session.add(strategy)
        db.session.flush()

        file_record = File(
            owner_id=None,
            filename=Path(package_path).name,
            content_type='application/zip',
            size=Path(package_path).stat().st_size,
            path=Path(package_path).as_posix(),
        )
        db.session.add(file_record)
        db.session.flush()

        strategy_version = StrategyVersion(
            strategy_id=strategy.id,
            version=version,
            file_id=file_record.id,
            checksum='descriptor-checksum',
        )
        db.session.add(strategy_version)
        db.session.commit()

    return strategy_id, version


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138020", nickname="StrategyUser"):
    _seed_code(client.application, phone)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _build_qys_package(
    tmp_path,
    *,
    strategy_id=None,
    version="1.0.0",
    name="Imported Strategy",
    description="Package import test",
    tags=None,
    category="trend-following",
    source_code=None,
    tamper_integrity=False,
):
    strategy_id = strategy_id or str(uuid.uuid4())
    tags = tags or ["gold", "trend"]
    source_code = source_code or (
        "class Strategy:\n"
        "    def on_bar(self, ctx, bar):\n"
        "        return None\n"
    )
    source_bytes = source_code.encode("utf-8")
    sha256 = "0" * 64 if tamper_integrity else hashlib.sha256(source_bytes).hexdigest()
    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": name,
        "version": version,
        "description": description,
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
        "tags": tags,
        "ui": {"category": category, "difficulty": "beginner"},
        "integrity": {
            "files": [
                {
                    "path": "src/strategy.py",
                    "sha256": sha256,
                    "size": len(source_bytes),
                }
            ]
        },
    }
    package_path = tmp_path / f"{strategy_id}-{version}.qys"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("strategy.json", json.dumps(manifest))
        archive.writestr("src/strategy.py", source_code)
    return package_path, manifest, source_code


def test_recent_strategies(client):
    resp = client.get('/api/strategies/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)


def test_runtime_descriptor_returns_parameters(client, app, tmp_path):
    strategy_id, version = _seed_runtime_strategy(app, tmp_path)
    resp = client.get(f'/api/strategies/{strategy_id}/runtime?version={version}')

    assert resp.status_code == 200
    data = resp.json['data']
    assert data['strategyId'] == strategy_id
    assert data['strategyVersion'] == version
    assert data['interface'] == 'event_v1'
    assert len(data['parameters']) == 2


def test_get_strategy_parameters_returns_normalized_manifest_parameters(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138026", nickname="ParameterOwner")
    strategy_id, _ = _seed_runtime_strategy(
        app,
        tmp_path,
        owner_id=user_id,
        parameters=[
            {
                "key": "window",
                "type": "integer",
                "default": 20,
                "min": 5,
                "max": 200,
                "step": 1,
                "description": "Lookback period",
            },
            {
                "name": "trade_direction",
                "type": "string",
                "default": "long",
                "options": ["long", "short", "both"],
                "description": "Trade direction",
            },
        ],
    )

    response = client.get(
        f"/api/v1/strategies/{strategy_id}/parameters",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data == [
        {
            "name": "window",
            "type": "int",
            "default": 20,
            "min": 5,
            "max": 200,
            "step": 1,
            "description": "Lookback period",
            "options": None,
            "required": False,
        },
        {
            "name": "trade_direction",
            "type": "enum",
            "default": "long",
            "min": None,
            "max": None,
            "step": None,
            "description": "Trade direction",
            "options": ["long", "short", "both"],
            "required": False,
        },
    ]


def test_marketplace_strategies_can_filter_onboarding_tag(client, app):
    with app.app_context():
        db.session.add_all(
            [
                Strategy(
                    id="guided-strategy",
                    name="Guided Gold Strategy",
                    symbol="XAUUSD",
                    status="running",
                    owner_id=None,
                    returns=12.5,
                    win_rate=68,
                    max_drawdown=9.8,
                    tags=["onboarding", "gold"],
                    trades=18,
                ),
                Strategy(
                    id="non-guided-strategy",
                    name="Other Strategy",
                    symbol="BTCUSDT",
                    status="running",
                    owner_id=None,
                    returns=4.2,
                    win_rate=55,
                    max_drawdown=11.3,
                    tags=["swing"],
                    trades=6,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?tag=onboarding")

    assert response.status_code == 200
    items = response.json["data"]
    assert [item["id"] for item in items] == ["guided-strategy"]
    assert items[0]["tags"] == ["onboarding", "gold"]


def test_import_strategy_encrypts_entrypoint_source(client, app, tmp_path):
    strategy_id = str(uuid.uuid4())
    version = '2.0.0'
    package_path = tmp_path / 'encrypted-import.qys'
    source = """
class Strategy:
    def on_bar(self, ctx, bar):
        return None
"""
    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": "Encrypted Import Strategy",
        "version": version,
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
    }

    with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('strategy.json', json.dumps(manifest))
        archive.writestr('src/strategy.py', source)

    with package_path.open('rb') as handle:
        response = client.post(
            '/api/strategies/import',
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type='multipart/form-data',
        )

    assert response.status_code == 200

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        assert strategy is not None
        assert strategy.code_encrypted is not None
        assert strategy.code_encrypted != source.encode('utf-8')
        assert strategy.code_hash is not None


def test_list_strategies_returns_only_current_user_with_pagination(client, app):
    token, user_id = _login_user(client, phone="13800138021", nickname="ListOwner")
    _, other_user_id = _login_user(client, phone="13800138022", nickname="OtherOwner")

    with app.app_context():
        db.session.add_all(
            [
                Strategy(
                    id="strategy-a",
                    name="Alpha",
                    symbol="BTCUSDT",
                    status="draft",
                    owner_id=user_id,
                    tags=["a"],
                    created_at=100,
                ),
                Strategy(
                    id="strategy-b",
                    name="Beta",
                    symbol="ETHUSDT",
                    status="draft",
                    owner_id=user_id,
                    tags=["b"],
                    created_at=200,
                ),
                Strategy(
                    id="strategy-c",
                    name="Gamma",
                    symbol="XAUUSD",
                    status="draft",
                    owner_id=other_user_id,
                    tags=["c"],
                    created_at=300,
                ),
                Strategy(
                    id="strategy-d",
                    name="Shared",
                    symbol="AAPL",
                    status="draft",
                    owner_id=None,
                    tags=["d"],
                    created_at=400,
                ),
            ]
        )
        db.session.commit()

    response = client.get(
        "/api/v1/strategies/?page=1&per_page=1&sort=created_at&order=desc",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["page"] == 1
    assert data["perPage"] == 1
    assert data["total"] == 2
    assert [item["id"] for item in data["items"]] == ["strategy-b"]
    assert data["items"][0]["source"] == "upload"


def test_delete_strategy_requires_owner_and_cleans_relations(client, app, tmp_path):
    owner_token, owner_id = _login_user(client, phone="13800138023", nickname="DeleteOwner")
    intruder_token, intruder_id = _login_user(client, phone="13800138024", nickname="Intruder")

    package_path, _, source_code = _build_qys_package(tmp_path, strategy_id="delete-me")

    with app.app_context():
        strategy = Strategy(
            id="delete-me",
            name="Delete Me",
            symbol="BTCUSDT",
            status="draft",
            owner_id=owner_id,
            code_encrypted=source_code.encode("utf-8"),
            code_hash="hash",
        )
        db.session.add(strategy)
        db.session.flush()
        file_record = File(
            owner_id=owner_id,
            filename=package_path.name,
            content_type="application/zip",
            size=package_path.stat().st_size,
            path=package_path.as_posix(),
        )
        db.session.add(file_record)
        db.session.flush()
        db.session.add(StrategyVersion(strategy_id=strategy.id, version="1.0.0", file_id=file_record.id, checksum="sum"))
        db.session.add(BacktestJob(user_id=owner_id, strategy_id=strategy.id, status="completed", params={"symbol": "BTCUSDT"}))
        db.session.commit()

    forbidden = client.delete("/api/v1/strategies/delete-me", headers=_auth_headers(intruder_token))
    assert forbidden.status_code == 404
    assert forbidden.json["error"]["code"] == "STRATEGY_NOT_FOUND"

    response = client.delete("/api/v1/strategies/delete-me", headers=_auth_headers(owner_token))

    assert response.status_code == 200
    assert response.json["data"]["deletedId"] == "delete-me"

    with app.app_context():
        assert db.session.get(Strategy, "delete-me") is None
        assert StrategyVersion.query.filter_by(strategy_id="delete-me").count() == 0
        assert BacktestJob.query.filter_by(strategy_id="delete-me").count() == 0
        assert File.query.filter_by(filename=package_path.name).count() == 0
    assert not package_path.exists()


def test_import_strategy_requires_auth(client, tmp_path):
    package_path, _, _ = _build_qys_package(tmp_path)
    with package_path.open("rb") as handle:
        response = client.post(
            "/api/v1/strategies/import",
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_import_strategy_creates_owned_strategy_and_returns_metadata(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138025", nickname="Importer")
    package_path, manifest, source_code = _build_qys_package(
        tmp_path,
        strategy_id="imported-strategy",
        name="Golden Cross",
        description="Trend strategy for gold",
        tags=["gold", "trend"],
        category="trend-following",
    )

    with package_path.open("rb") as handle:
        response = client.post(
            "/api/v1/strategies/import",
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["strategy"]["id"] == "imported-strategy"
    assert data["strategy"]["name"] == "Golden Cross"
    assert data["strategy"]["description"] == "Trend strategy for gold"
    assert data["strategy"]["tags"] == ["gold", "trend"]
    assert data["strategy"]["category"] == "trend-following"
    assert data["strategy"]["source"] == "upload"
    assert data["next"] == "/strategies/imported-strategy/parameters"

    with app.app_context():
        strategy = db.session.get(Strategy, "imported-strategy")
        assert strategy is not None
        assert strategy.owner_id == user_id
        assert strategy.code_encrypted is not None
        assert strategy.code_encrypted != source_code.encode("utf-8")
        assert strategy.code_hash is not None
        assert strategy.storage_key
        assert strategy.description == manifest["description"]
        assert strategy.category == "trend-following"
        assert File.query.filter_by(owner_id=user_id).count() == 1
        assert StrategyVersion.query.filter_by(strategy_id="imported-strategy").count() == 1


def test_import_strategy_returns_422_when_integrity_check_fails(client, tmp_path):
    token, _ = _login_user(client, phone="13800138026", nickname="IntegrityUser")
    package_path, _, _ = _build_qys_package(tmp_path, tamper_integrity=True)

    with package_path.open("rb") as handle:
        response = client.post(
            "/api/v1/strategies/import",
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "INTEGRITY_CHECK_FAILED"
