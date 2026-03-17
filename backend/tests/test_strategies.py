
import io
import json
import uuid
import zipfile
from pathlib import Path

from app.extensions import db
from app.models import File, Strategy, StrategyVersion


def _seed_runtime_strategy(app, tmp_path):
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
        "parameters": [
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
