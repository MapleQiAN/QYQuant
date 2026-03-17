import json
import uuid
import zipfile
from pathlib import Path

from app.extensions import db
from app.models import File, Strategy, StrategyVersion


def _build_qys(tmp_path, strategy_id, version='1.0.0', strategy_source=None, parameters=None):
    package_path = tmp_path / f'{strategy_id}-{version}.qys'
    source = strategy_source or '''
class Strategy:
    def __init__(self, ctx=None):
        self.ctx = ctx

    def on_init(self, ctx):
        return None

    def on_bar(self, ctx, bar):
        if bar["close"] > bar["open"]:
            ctx.emit_order({"side": "buy", "price": bar["close"], "quantity": 1})

    def on_finish(self, ctx, result):
        return None
'''
    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": "Runtime Test Strategy",
        "version": version,
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
        "parameters": parameters
        or [
            {
                "key": "threshold",
                "type": "number",
                "default": 0.2,
                "required": True,
                "min": 0,
                "max": 1,
            }
        ],
    }

    with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('strategy.json', json.dumps(manifest))
        archive.writestr('src/strategy.py', source)

    return package_path


def _seed_strategy_version(app, strategy_id, version, package_path):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            name='Runtime Test Strategy',
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
            checksum='test-checksum',
        )
        db.session.add(strategy_version)
        db.session.commit()


def test_missing_strategy_version_returns_400(client):
    payload = {
        "symbol": "BTCUSDT",
        "strategyId": str(uuid.uuid4()),
        "strategyVersion": "1.0.0",
        "strategyParams": {"threshold": 0.2},
    }
    response = client.post('/api/backtests/run', json=payload)
    assert response.status_code == 400
    assert response.json['message'] == 'strategy_version_not_found'


def test_param_validation_range_error(client, app, tmp_path):
    strategy_id = str(uuid.uuid4())
    version = '1.0.0'
    package_path = _build_qys(tmp_path, strategy_id, version=version)
    _seed_strategy_version(app, strategy_id, version, package_path)

    payload = {
        "symbol": "BTCUSDT",
        "strategyId": strategy_id,
        "strategyVersion": version,
        "strategyParams": {"threshold": 2},
    }
    response = client.post('/api/backtests/run', json=payload)
    assert response.status_code == 400
    assert response.json['message'] == 'invalid_strategy_params'


def test_runtime_executes_strategy_package(client, app, tmp_path):
    strategy_id = str(uuid.uuid4())
    version = '1.0.0'
    package_path = _build_qys(tmp_path, strategy_id, version=version)
    _seed_strategy_version(app, strategy_id, version, package_path)

    payload = {
        "symbol": "BTCUSDT",
        "strategyId": strategy_id,
        "strategyVersion": version,
        "strategyParams": {"threshold": 0.1},
    }
    response = client.post('/api/backtests/run', json=payload)

    assert response.status_code == 200
    job_id = response.json['data']['job_id']

    status = client.get(f'/api/backtests/job/{job_id}')
    assert status.status_code == 200
    assert status.json['data']['status'] == 'completed'
    result = status.json['data']['result']
    assert len(result['trades']) > 0
    assert result['runtime']['strategyId'] == strategy_id
    assert result['runtime']['strategyVersion'] == version


def test_forbidden_import_rejected(client, app, tmp_path):
    strategy_id = str(uuid.uuid4())
    version = '1.0.1'
    source = '''
import os

class Strategy:
    def on_bar(self, ctx, bar):
        return None
'''
    package_path = _build_qys(tmp_path, strategy_id, version=version, strategy_source=source)
    _seed_strategy_version(app, strategy_id, version, package_path)

    payload = {
        "symbol": "BTCUSDT",
        "strategyId": strategy_id,
        "strategyVersion": version,
        "strategyParams": {"threshold": 0.2},
    }
    response = client.post('/api/backtests/run', json=payload)
    assert response.status_code == 400
    assert response.json['message'] == 'sandbox_rejected'

