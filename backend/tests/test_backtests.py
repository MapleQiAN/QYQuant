from celery.exceptions import SoftTimeLimitExceeded


def _seed_runtime_strategy(app, tmp_path, strategy_id='sandbox-strategy', version='1.0.0'):
    import json
    import zipfile
    from pathlib import Path

    from app.extensions import db
    from app.models import File, Strategy, StrategyVersion
    from app.utils.crypto import encrypt_strategy, hash_strategy_source

    package_path = tmp_path / f'{strategy_id}-{version}.qys'
    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": "Sandbox Runtime Strategy",
        "version": version,
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
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
            name='Sandbox Runtime Strategy',
            symbol='BTCUSDT',
            status='draft',
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=['sandbox'],
            trades=0,
            code_encrypted=encrypt_strategy(source.encode('utf-8')),
            code_hash=hash_strategy_source(source),
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
            checksum='runtime-checksum',
        )
        db.session.add(strategy_version)
        db.session.commit()

    return strategy_id, version


def test_backtest_run_persists_completed_job_and_query_reads_database(client, app):
    from app.extensions import db
    from app.models import BacktestJob

    resp = client.post('/api/backtests/run', json={"symbol": "BTCUSDT", "limit": 20})

    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job is not None
        assert job.status == 'completed'
        assert job.params['symbol'] == 'BTCUSDT'
        assert job.result_summary is not None

    status = client.get(f'/api/backtests/job/{job_id}')
    assert status.status_code == 200
    assert status.json['data']['job_id'] == job_id
    assert status.json['data']['status'] == 'completed'
    assert status.json['data']['result_summary'] is not None


def test_backtest_run_marks_failed_jobs(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    def _raise_failure(*args, **kwargs):
        raise RuntimeError('boom')

    monkeypatch.setattr('app.tasks.backtests.run_backtest', _raise_failure)

    resp = client.post('/api/backtests/run', json={"symbol": "BTCUSDT"})
    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job.status == 'failed'
        assert 'boom' in job.error_message


def test_backtest_run_marks_timeout_jobs(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    def _raise_timeout(*args, **kwargs):
        raise SoftTimeLimitExceeded()

    monkeypatch.setattr('app.tasks.backtests.run_backtest', _raise_timeout)

    resp = client.post('/api/backtests/run', json={"symbol": "BTCUSDT"})
    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job.status == 'timeout'
        assert job.error_message


def test_failed_job_does_not_block_later_job(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    call_count = {'count': 0}

    def _flaky(symbol, **kwargs):
        call_count['count'] += 1
        if call_count['count'] == 1:
            raise RuntimeError('first failed')
        return {
            'summary': {'totalReturn': 1},
            'kline': [],
            'trades': [],
            'dataSource': 'mock',
        }

    monkeypatch.setattr('app.tasks.backtests.run_backtest', _flaky)

    first = client.post('/api/backtests/run', json={"symbol": "BTCUSDT"})
    second = client.post('/api/backtests/run', json={"symbol": "ETHUSDT"})

    with app.app_context():
        failed = db.session.get(BacktestJob, first.json['data']['job_id'])
        completed = db.session.get(BacktestJob, second.json['data']['job_id'])
        assert failed.status == 'failed'
        assert completed.status == 'completed'


def test_backtest_latest_remains_synchronous_debug_endpoint(client):
    resp = client.get('/api/backtests/latest?symbol=BTCUSDT&limit=10')

    assert resp.status_code == 200
    assert resp.json['data']['summary'] is not None
    assert 'job_id' not in resp.json['data']


def test_backtest_run_executes_strategy_via_sandbox(monkeypatch, client, app, tmp_path):
    strategy_id, version = _seed_runtime_strategy(app, tmp_path)

    monkeypatch.setattr(
        'app.services.sandbox.execute_strategy',
        lambda code, market_data, params, metadata=None: {
            'trades': [
                {"symbol": "BTCUSDT", "side": "buy", "price": 101.0, "quantity": 1, "timestamp": 1, "pnl": None}
            ],
            'logs': ['sandbox-ok'],
        },
    )

    response = client.post(
        '/api/backtests/run',
        json={
            "symbol": "BTCUSDT",
            "strategyId": strategy_id,
            "strategyVersion": version,
            "strategyParams": {"window": 5},
        },
    )

    assert response.status_code == 200
    job_id = response.json['data']['job_id']

    status = client.get(f'/api/backtests/job/{job_id}')
    assert status.status_code == 200
    assert status.json['data']['status'] == 'completed'
    assert status.json['data']['result']['runtime']['logs'] == ['sandbox-ok']
    assert status.json['data']['result']['trades'][0]['side'] == 'buy'


def test_backtest_run_marks_strategy_timeout_jobs(monkeypatch, client, app, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob
    from app.strategy_runtime.errors import StrategyRuntimeError

    strategy_id, version = _seed_runtime_strategy(app, tmp_path, strategy_id='timeout-strategy')

    def _raise_timeout(*args, **kwargs):
        raise StrategyRuntimeError('strategy_timeout')

    monkeypatch.setattr('app.services.sandbox.execute_strategy', _raise_timeout)

    response = client.post(
        '/api/backtests/run',
        json={
            "symbol": "BTCUSDT",
            "strategyId": strategy_id,
            "strategyVersion": version,
        },
    )

    assert response.status_code == 200
    job_id = response.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job.status == 'timeout'
