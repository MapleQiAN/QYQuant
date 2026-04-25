
import hashlib
import io
import json
import uuid
import zipfile
from datetime import timedelta
from pathlib import Path

from app.extensions import db
from app.models import (
    BacktestJob,
    File,
    IntegrationProvider,
    Strategy,
    StrategyImportDraft,
    StrategyVersion,
    UserIntegration,
    UserIntegrationSecret,
)
from app.utils.time import now_utc
from qysp.validator import validate_integrity


def _seed_runtime_strategy(app, tmp_path, *, owner_id=None, parameters=None, is_public=False, review_status='draft'):
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
            is_public=is_public,
            review_status=review_status,
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


def _build_source_zip_bytes(*, include_manifest=True, include_requirements=False, source_code=None, parameters=None):
    source_code = source_code or (
        "class Strategy:\n"
        "    def on_bar(self, ctx, bar):\n"
        "        return None\n"
    )
    payload = io.BytesIO()
    manifest = None
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if include_manifest:
            manifest = {
                "schemaVersion": "1.0",
                "kind": "QYStrategy",
                "id": str(uuid.uuid4()),
                "name": "Zip Imported Strategy",
                "version": "0.1.0",
                "description": "Zip source import",
                "language": "python",
                "runtime": {"name": "python", "version": "3.11"},
                "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
                "parameters": parameters or [{"key": "window", "type": "integer", "default": 20}],
                "tags": ["zip", "source"],
                "ui": {"category": "trend-following"},
            }
            archive.writestr("strategy.json", json.dumps(manifest))
        archive.writestr("src/strategy.py", source_code)
        if include_requirements:
            archive.writestr("requirements.txt", "pandas==2.2.3\n")
    payload.seek(0)
    return payload, manifest


def test_recent_strategies(client):
    resp = client.get('/api/strategies/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)


def test_strategy_import_draft_persists_analysis_payload(app):
    with app.app_context():
        source_file = File(
            owner_id="draft-owner",
            filename="draft-source.zip",
            content_type="application/zip",
            size=128,
            path="/tmp/draft-source.zip",
        )
        db.session.add(source_file)
        db.session.flush()

        expires_at = now_utc() + timedelta(hours=1)
        draft = StrategyImportDraft(
            owner_id="draft-owner",
            source_file_id=source_file.id,
            source_type="source_zip",
            status="analyzed",
            analysis_payload={
                "entrypointCandidates": [{"path": "src/strategy.py", "callable": "Strategy"}],
                "warnings": ["ignored requirements.txt"],
            },
            expires_at=expires_at,
        )
        db.session.add(draft)
        db.session.commit()

        saved = db.session.get(StrategyImportDraft, draft.id)
        assert saved is not None
        assert saved.source_file_id == source_file.id
        assert saved.source_type == "source_zip"
        assert saved.status == "analyzed"
        assert saved.analysis_payload["warnings"] == ["ignored requirements.txt"]
        assert saved.expires_at == expires_at.replace(tzinfo=None)


def test_strategy_persists_original_and_built_package_file_links(app):
    with app.app_context():
        original_source = File(
            owner_id="owner-1",
            filename="source.zip",
            content_type="application/zip",
            size=256,
            path="/tmp/source.zip",
        )
        built_package = File(
            owner_id="owner-1",
            filename="strategy.qys",
            content_type="application/zip",
            size=512,
            path="/tmp/strategy.qys",
        )
        db.session.add_all([original_source, built_package])
        db.session.flush()

        strategy = Strategy(
            id="strategy-with-file-links",
            name="Linked Strategy",
            symbol="XAUUSD",
            status="draft",
            owner_id="owner-1",
            original_source_file_id=original_source.id,
            built_package_file_id=built_package.id,
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=["draft"],
            trades=0,
        )
        db.session.add(strategy)
        db.session.commit()

        saved = db.session.get(Strategy, "strategy-with-file-links")
        assert saved is not None
        assert saved.original_source_file_id == original_source.id
        assert saved.built_package_file_id == built_package.id


def test_runtime_descriptor_returns_parameters(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138024", nickname="RuntimeDescriptorOwner")
    strategy_id, version = _seed_runtime_strategy(app, tmp_path, owner_id=user_id)
    resp = client.get(
        f'/api/strategies/{strategy_id}/runtime?version={version}',
        headers=_auth_headers(token),
    )

    assert resp.status_code == 200
    data = resp.json['data']
    assert data['strategyId'] == strategy_id
    assert data['strategyVersion'] == version
    assert data['interface'] == 'event_v1'
    assert len(data['parameters']) == 2


def test_runtime_descriptor_hides_private_strategy_from_unauthenticated_calls(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138025", nickname="RuntimePrivateOwner")
    strategy_id, version = _seed_runtime_strategy(app, tmp_path, owner_id=user_id)

    authed = client.get(
        f'/api/strategies/{strategy_id}/runtime?version={version}',
        headers=_auth_headers(token),
    )
    anonymous = client.get(f'/api/strategies/{strategy_id}/runtime?version={version}')

    assert authed.status_code == 200
    assert anonymous.status_code == 404
    assert anonymous.json["error"]["code"] == "STRATEGY_NOT_FOUND"


def test_runtime_descriptor_allows_public_strategy_without_auth(client, app, tmp_path):
    strategy_id, version = _seed_runtime_strategy(
        app,
        tmp_path,
        is_public=True,
        review_status="approved",
    )

    response = client.get(f'/api/strategies/{strategy_id}/runtime?version={version}')

    assert response.status_code == 200
    assert response.json["data"]["strategyVersion"] == version


def test_analyze_strategy_import_for_python_file_persists_draft(client, app):
    token, user_id = _login_user(client, phone="13800138031", nickname="AnalyzePyUser")
    source = (
        "class Strategy:\n"
        "    def on_bar(self, ctx, bar):\n"
        "        return None\n"
    )

    response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "strategy.py")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["sourceType"] == "python_file"
    assert data["draftImportId"]
    assert data["errors"] == []
    assert data["entrypointCandidates"] == [
        {
            "path": "strategy.py",
            "callable": "Strategy",
            "interface": "event_v1",
            "confidence": 0.9,
        }
    ]

    with app.app_context():
        draft = db.session.get(StrategyImportDraft, data["draftImportId"])
        assert draft is not None
        assert draft.owner_id == user_id
        assert draft.source_type == "python_file"
        assert draft.analysis_payload["entrypointCandidates"][0]["callable"] == "Strategy"


def test_analyze_strategy_import_for_source_zip_reads_manifest_and_warnings(client, app):
    token, user_id = _login_user(client, phone="13800138032", nickname="AnalyzeZipUser")
    payload, manifest = _build_source_zip_bytes(include_manifest=True, include_requirements=True)

    response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (payload, "strategy-project.zip")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["sourceType"] == "source_zip"
    assert data["metadataCandidates"]["name"] == manifest["name"]
    assert data["metadataCandidates"]["category"] == "trend-following"
    assert data["parameterCandidates"] == manifest["parameters"]
    assert data["warnings"] == ["Ignored unsupported dependency manifest: requirements.txt"]
    assert data["errors"] == []

    with app.app_context():
        draft = db.session.get(StrategyImportDraft, data["draftImportId"])
        assert draft is not None
        assert draft.owner_id == user_id
        assert draft.analysis_payload["warnings"] == ["Ignored unsupported dependency manifest: requirements.txt"]


def test_analyze_strategy_import_for_qys_reads_package_manifest(client):
    token, _ = _login_user(client, phone="13800138033", nickname="AnalyzeQysUser")
    payload, manifest = _build_source_zip_bytes(include_manifest=True)

    response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (payload, "ready-package.qys")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["sourceType"] == "qys_package"
    assert data["metadataCandidates"]["name"] == manifest["name"]
    assert data["entrypointCandidates"][0]["path"] == "src/strategy.py"
    assert data["parameterCandidates"] == manifest["parameters"]


def test_analyze_strategy_import_reports_blocking_errors_for_unsupported_layout(client):
    token, _ = _login_user(client, phone="13800138034", nickname="AnalyzeBlockedUser")
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", "No strategy code here")
    payload.seek(0)

    response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (payload, "empty-project.zip")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["sourceType"] == "source_zip"
    assert data["entrypointCandidates"] == []
    assert data["errors"] == ["No supported strategy entrypoint candidates found"]


def test_analyze_strategy_import_reports_python_syntax_validation(client):
    token, _ = _login_user(client, phone="13800138039", nickname="AnalyzeSyntaxUser")
    invalid_source = "def on_bar(ctx, data):\n    if data.close > data.open\n        return []\n"

    response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(invalid_source.encode("utf-8")), "broken.py")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["entrypointCandidates"] == []
    assert data["errors"] == ["Python syntax could not be parsed"]
    assert data["validation"] == {
        "entrypointFound": False,
        "pythonSyntaxValid": False,
        "orderListReturnLikely": None,
        "metadataDetected": True,
    }


def test_generate_ai_strategy_creates_import_draft_from_user_integration(client, app, monkeypatch):
    token, user_id = _login_user(client, phone="13800138040", nickname="AiDraftUser")

    with app.app_context():
        provider = IntegrationProvider(
            key="openai_compatible",
            name="OpenAI Compatible",
            type="llm",
            mode="hosted",
            capabilities={"chat": True, "strategy_generation": True},
            config_schema={"public_fields": ["base_url", "model"], "secret_fields": ["api_key"]},
        )
        db.session.merge(provider)

        integration = UserIntegration(
            user_id=user_id,
            provider_key="openai_compatible",
            display_name="Strategy AI",
            status="active",
            config_public={"base_url": "https://example.com/v1", "model": "demo-model"},
        )
        db.session.add(integration)
        db.session.flush()
        db.session.add(
            UserIntegrationSecret(
                integration_id=integration.id,
                encrypted_payload="ciphertext",
                schema_version=1,
            )
        )
        db.session.commit()
        integration_id = integration.id

    from app.services import ai_strategy_generation as ai_generation_service
    monkeypatch.setattr(ai_generation_service, "decrypt_secret_payload", lambda integration: {"api_key": "secret-key"})
    monkeypatch.setattr(
        ai_generation_service,
        "_request_chat_completion",
        lambda **kwargs: json.dumps(
            {
                "reply": "Draft ready. Review entry rules and ATR stop.",
                "strategy": {
                    "name": "AI Momentum Draft",
                    "description": "EMA trend following with ATR stop",
                    "category": "momentum",
                    "symbol": "BTCUSDT",
                    "tags": ["ai", "momentum"],
                    "parameters": [
                        {
                            "key": "fast_period",
                            "type": "integer",
                            "default": 10,
                            "min": 2,
                            "max": 50,
                            "user_facing": {
                                "question": "How sensitive should the fast EMA be?",
                                "options": [
                                    {"label": "Fast", "value": 8},
                                    {"label": "Balanced", "value": 10},
                                ],
                            },
                        },
                        {"key": "slow_period", "type": "integer", "default": 30, "min": 5, "max": 120},
                    ],
                    "code": (
                        "from qysp import BarData, Order, StrategyContext\n\n"
                        "def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:\n"
                        "    fast_period = int(ctx.parameters.get('fast_period', 10))\n"
                        "    slow_period = int(ctx.parameters.get('slow_period', 30))\n"
                        "    prices = list(getattr(ctx, '_prices', []))\n"
                        "    prices.append(float(data.close))\n"
                        "    prices = prices[-slow_period:]\n"
                        "    setattr(ctx, '_prices', prices)\n"
                        "    if len(prices) < slow_period or fast_period >= slow_period:\n"
                        "        return []\n"
                        "    fast_ma = sum(prices[-fast_period:]) / fast_period\n"
                        "    slow_ma = sum(prices) / slow_period\n"
                        "    if fast_ma > slow_ma:\n"
                        "        return [ctx.buy(data.symbol, quantity=1)]\n"
                        "    return []\n"
                    ),
                },
            }
        ),
    )

    response = client.post(
        "/api/v1/strategy-ai/generate",
        headers=_auth_headers(token),
        json={
            "integrationId": integration_id,
            "messages": [{"role": "user", "content": "Build a BTC trend strategy with EMA crossover"}],
        },
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["reply"] == "Draft ready. Review entry rules and ATR stop."
    assert data["analysis"]["metadataCandidates"]["name"] == "AI Momentum Draft"
    assert data["analysis"]["metadataCandidates"]["symbol"] == "BTCUSDT"
    assert data["analysis"]["parameterCandidates"] == [
        {
            "key": "fast_period",
            "type": "integer",
            "default": 10,
            "min": 2,
            "max": 50,
            "user_facing": {
                "question": "How sensitive should the fast EMA be?",
                "options": [
                    {"label": "Fast", "value": 8},
                    {"label": "Balanced", "value": 10},
                ],
            },
        },
        {"key": "slow_period", "type": "integer", "default": 30, "min": 5, "max": 120},
    ]
    assert data["analysis"]["errors"] == []
    assert data["analysis"]["entrypointCandidates"] == [
        {
            "path": "ai-momentum-draft.py",
            "callable": "on_bar",
            "interface": "event_v1",
            "confidence": 0.8,
        }
    ]

    with app.app_context():
        draft = db.session.get(StrategyImportDraft, data["analysis"]["draftImportId"])
        assert draft is not None
        assert draft.owner_id == user_id
        assert draft.analysis_payload["metadataCandidates"]["category"] == "momentum"


def test_confirm_strategy_import_uses_selected_entrypoint_and_creates_final_package(client, app):
    token, user_id = _login_user(client, phone="13800138035", nickname="ConfirmPyUser")
    source = (
        "class Strategy:\n"
        "    def on_bar(self, ctx, bar):\n"
        "        return None\n\n"
        "def on_bar(ctx, bar):\n"
        "    return []\n"
    )

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "multi-entry.py")},
        content_type="multipart/form-data",
    )
    assert analyze_response.status_code == 200
    draft_import_id = analyze_response.json["data"]["draftImportId"]

    response = client.post(
        "/api/v1/strategy-imports/confirm",
        headers=_auth_headers(token),
        json={
            "draftImportId": draft_import_id,
            "selectedEntrypoint": {
                "path": "multi-entry.py",
                "callable": "on_bar",
                "interface": "event_v1",
            },
            "metadata": {
                "name": "Confirmed Python Strategy",
                "description": "Manual confirmation for python upload",
                "category": "momentum",
                "tags": ["python", "confirmed"],
                "symbol": "BTCUSDT",
            },
            "parameterDefinitions": [{"key": "window", "type": "integer", "default": 12}],
        },
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["strategy"]["name"] == "Confirmed Python Strategy"
    assert data["strategy"]["originalSourceFileId"]
    assert data["strategy"]["builtPackageFileId"] == data["file"]["id"]
    assert data["next"] == f"/strategies/{data['strategy']['id']}/parameters"

    with app.app_context():
        strategy = db.session.get(Strategy, data["strategy"]["id"])
        assert strategy is not None
        assert strategy.owner_id == user_id
        assert strategy.original_source_file_id is not None
        assert strategy.built_package_file_id is not None
        assert StrategyVersion.query.filter_by(strategy_id=strategy.id).count() == 1

        built_file = db.session.get(File, strategy.built_package_file_id)
        assert built_file is not None
        assert validate_integrity(built_file.path) is True
        with zipfile.ZipFile(built_file.path, "r") as archive:
            manifest = json.loads(archive.read("strategy.json").decode("utf-8"))
        assert manifest["entrypoint"]["callable"] == "on_bar"
        assert manifest["entrypoint"]["path"] == "src/strategy.py"


def test_confirm_strategy_import_fills_missing_metadata_from_payload(client, app):
    token, user_id = _login_user(client, phone="13800138036", nickname="ConfirmZipUser")
    payload, _ = _build_source_zip_bytes(include_manifest=False)

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (payload, "source-only.zip")},
        content_type="multipart/form-data",
    )
    assert analyze_response.status_code == 200
    draft_import_id = analyze_response.json["data"]["draftImportId"]

    response = client.post(
        "/api/v1/strategy-imports/confirm",
        headers=_auth_headers(token),
        json={
            "draftImportId": draft_import_id,
            "selectedEntrypoint": {
                "path": "src/strategy.py",
                "callable": "Strategy",
                "interface": "event_v1",
            },
            "metadata": {
                "name": "Zip Confirmed Strategy",
                "description": "Filled in at confirmation time",
                "category": "trend-following",
                "tags": ["zip", "confirmed"],
                "symbol": "XAUUSD",
                "version": "2.1.0",
            },
            "parameterDefinitions": [
                {
                    "key": "threshold",
                    "type": "number",
                    "default": 1.5,
                    "user_facing": {
                        "question": "How aggressive should entries be?",
                        "options": [
                            {"label": "Conservative", "value": 1.0},
                            {"label": "Balanced", "value": 1.5},
                        ],
                    },
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["strategy"]["name"] == "Zip Confirmed Strategy"
    assert data["strategy"]["description"] == "Filled in at confirmation time"
    assert data["strategy"]["category"] == "trend-following"

    with app.app_context():
        strategy = db.session.get(Strategy, data["strategy"]["id"])
        assert strategy is not None
        assert strategy.owner_id == user_id
        assert strategy.original_source_file_id is not None
        assert strategy.built_package_file_id is not None

        built_file = db.session.get(File, strategy.built_package_file_id)
        with zipfile.ZipFile(built_file.path, "r") as archive:
            manifest = json.loads(archive.read("strategy.json").decode("utf-8"))
        assert manifest["name"] == "Zip Confirmed Strategy"
        assert manifest["description"] == "Filled in at confirmation time"
        assert manifest["version"] == "2.1.0"
        assert manifest["parameters"] == [
            {
                "key": "threshold",
                "type": "number",
                "default": 1.5,
                "user_facing": {
                    "question": "How aggressive should entries be?",
                    "options": [
                        {"label": "Conservative", "value": 1.0},
                        {"label": "Balanced", "value": 1.5},
                    ],
                },
            }
        ]

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
                "user_facing": {
                    "question": "How quickly should the signal react?",
                    "options": [
                        {"label": "Fast", "value": 10},
                        {"label": "Standard", "value": 20},
                    ],
                },
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
            "userFacing": {
                "question": "How quickly should the signal react?",
                "options": [
                    {"label": "Fast", "value": 10},
                    {"label": "Standard", "value": 20},
                ],
            },
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
            "userFacing": None,
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
                    is_public=True,
                    is_verified=True,
                    review_status="approved",
                    display_metrics={"totalReturn": 12.5},
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
                    is_public=True,
                    review_status="approved",
                    display_metrics={"totalReturn": 4.2},
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
    token, user_id = _login_user(client, phone="13800138027", nickname="EncryptUser")
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
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type='multipart/form-data',
        )

    assert response.status_code == 200

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        assert strategy is not None
        assert strategy.owner_id == user_id
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
                    source="marketplace",
                    source_strategy_id="marketplace-origin",
                    import_mode="sealed",
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
    assert data["items"][0]["source"] == "marketplace"
    assert data["items"][0]["sourceStrategyId"] == "marketplace-origin"
    assert data["items"][0]["importMode"] == "sealed"


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


def test_fetch_draft_code_returns_source_for_python_file(client, app):
    token, user_id = _login_user(client, phone="13800138041", nickname="CodeFetchUser")
    source = "class Strategy:\n    def on_bar(self, ctx, bar):\n        return []\n"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "my_strategy.py")},
        content_type="multipart/form-data",
    )
    assert analyze_response.status_code == 200
    draft_id = analyze_response.json["data"]["draftImportId"]

    response = client.get(
        f"/api/v1/strategy-imports/{draft_id}/code",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json["data"]
    assert data["code"] == source
    assert data["filename"] == "my_strategy.py"


def test_fetch_draft_code_returns_404_for_missing_draft(client):
    token, _ = _login_user(client, phone="13800138042", nickname="CodeFetchMissing")
    response = client.get(
        "/api/v1/strategy-imports/nonexistent-draft-id/code",
        headers=_auth_headers(token),
    )
    assert response.status_code == 404


def test_fetch_draft_code_rejects_other_users_draft(client, app):
    token_a, _ = _login_user(client, phone="13800138043", nickname="CodeOwnerA")
    source = "def on_bar(ctx, bar): return []"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token_a),
        data={"file": (io.BytesIO(source.encode("utf-8")), "test.py")},
        content_type="multipart/form-data",
    )
    draft_id = analyze_response.json["data"]["draftImportId"]

    token_b, _ = _login_user(client, phone="13800138044", nickname="CodeOwnerB")
    response = client.get(
        f"/api/v1/strategy-imports/{draft_id}/code",
        headers=_auth_headers(token_b),
    )
    assert response.status_code == 404


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
    assert data["strategy"]["originalSourceFileId"] == data["file"]["id"]
    assert data["strategy"]["builtPackageFileId"] != data["file"]["id"]
    assert data["version"]["fileId"] == data["file"]["id"]

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
        assert strategy.original_source_file_id is not None
        assert strategy.built_package_file_id is not None
        assert File.query.filter_by(owner_id=user_id).count() == 2
        assert StrategyVersion.query.filter_by(strategy_id="imported-strategy").count() == 1


def test_legacy_import_v1_reuses_draft_pipeline(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138037", nickname="LegacyImporter")
    package_path, _, _ = _build_qys_package(tmp_path, strategy_id="legacy-v1-strategy")

    with package_path.open("rb") as handle:
        response = client.post(
            "/api/v1/strategies/import",
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    data = response.json["data"]

    with app.app_context():
        strategy = db.session.get(Strategy, data["strategy"]["id"])
        assert strategy is not None
        assert strategy.owner_id == user_id
        assert strategy.original_source_file_id is not None
        assert strategy.built_package_file_id is not None
        assert strategy.original_source_file_id != strategy.built_package_file_id

        draft = StrategyImportDraft.query.filter_by(
            owner_id=user_id,
            source_file_id=strategy.original_source_file_id,
        ).one_or_none()
        assert draft is not None
        assert draft.source_type == "qys_package"
        assert draft.status == "confirmed"


def test_legacy_import_compat_endpoint_reuses_draft_pipeline(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138038", nickname="LegacyCompatImporter")
    package_path, _, _ = _build_qys_package(tmp_path, strategy_id="legacy-compat-strategy")

    with package_path.open("rb") as handle:
        response = client.post(
            "/api/strategies/import",
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    data = response.json["data"]

    with app.app_context():
        strategy = db.session.get(Strategy, data["strategy"]["id"])
        assert strategy is not None
        assert strategy.owner_id == user_id
        assert strategy.original_source_file_id is not None
        assert strategy.built_package_file_id is not None

        draft = StrategyImportDraft.query.filter_by(
            owner_id=user_id,
            source_file_id=strategy.original_source_file_id,
        ).one_or_none()
        assert draft is not None
        assert draft.source_type == "qys_package"
        assert draft.status == "confirmed"


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


def test_import_strategy_returns_503_when_encryption_key_missing(client, monkeypatch, tmp_path):
    token, _ = _login_user(client, phone="13800138028", nickname="MissingKeyUser")
    package_path, _, _ = _build_qys_package(tmp_path)
    monkeypatch.delenv("STRATEGY_ENCRYPT_KEY", raising=False)

    with package_path.open("rb") as handle:
        response = client.post(
            "/api/v1/strategies/import",
            headers=_auth_headers(token),
            data={"file": (io.BytesIO(handle.read()), package_path.name)},
            content_type="multipart/form-data",
        )

    assert response.status_code == 503
    assert response.json["error"]["code"] == "STRATEGY_ENCRYPTION_UNAVAILABLE"
