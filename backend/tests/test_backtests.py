from celery.exceptions import SoftTimeLimitExceeded


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138000", nickname="Trader"):
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


def test_submit_backtest_requires_auth(client):
    response = client.post(
        "/api/v1/backtest/",
        json={
            "strategy_id": "missing",
            "symbols": ["BTCUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_submit_backtest_creates_pending_job_and_returns_job_id(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob, Strategy, UserQuota

    token, user_id = _login_user(client, phone="13800138001", nickname="Submitter")

    with app.app_context():
        strategy = Strategy(
            id="owned-strategy",
            name="Owned Strategy",
            symbol="BTCUSDT",
            status="draft",
            owner_id=user_id,
        )
        db.session.add(strategy)
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "free"
        quota.used_count = 0
        db.session.commit()

    queued = {}

    def _fake_apply_async(*args, **kwargs):
        queued["args"] = args
        queued["kwargs"] = kwargs
        return None

    monkeypatch.setattr("app.blueprints.backtests.run_backtest_task.apply_async", _fake_apply_async)

    response = client.post(
        "/api/v1/backtest/",
        headers=_auth_headers(token),
        json={
            "strategy_id": "owned-strategy",
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "parameters": {"window": 5},
        },
    )

    assert response.status_code == 200
    job_id = response.json["data"]["job_id"]
    assert isinstance(job_id, str)

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job is not None
        assert job.user_id == user_id
        assert job.strategy_id == "owned-strategy"
        assert job.status == "pending"
        assert job.params["symbols"] == ["BTCUSDT", "ETHUSDT"]
        assert job.params["start_date"] == "2024-01-01"
        assert job.params["end_date"] == "2024-01-31"

    assert queued["kwargs"]["task_id"] == job_id
    assert queued["kwargs"]["queue"] == "backtest"


def test_submit_backtest_returns_429_when_quota_exceeded(monkeypatch, client, app):
    from app.extensions import db
    from app.models import Strategy, UserQuota

    token, user_id = _login_user(client, phone="13800138002", nickname="QuotaUser")

    with app.app_context():
        db.session.add(
            Strategy(
                id="quota-strategy",
                name="Quota Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "free"
        quota.used_count = 10
        db.session.commit()

    monkeypatch.setattr("app.blueprints.backtests.run_backtest_task.apply_async", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/backtest/",
        headers=_auth_headers(token),
        json={
            "strategy_id": "quota-strategy",
            "symbols": ["BTCUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )

    assert response.status_code == 429
    assert response.json["error"]["code"] == "QUOTA_EXCEEDED"


def test_get_backtest_job_returns_estimated_wait_time_for_owner(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy, UserQuota

    token, user_id = _login_user(client, phone="13800138003", nickname="Owner")

    with app.app_context():
        db.session.add(
            Strategy(
                id="status-strategy",
                name="Status Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "free"
        quota.used_count = 0
        db.session.add(BacktestJob(user_id=user_id, strategy_id="status-strategy", status=BacktestJobStatus.PENDING.value))
        db.session.commit()

    monkeypatch.setattr("app.blueprints.backtests.run_backtest_task.apply_async", lambda *args, **kwargs: None)
    submit_response = client.post(
        "/api/v1/backtest/",
        headers=_auth_headers(token),
        json={
            "strategy_id": "status-strategy",
            "symbols": ["BTCUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    job_id = submit_response.json["data"]["job_id"]

    response = client.get(f"/api/v1/backtest/{job_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["job_id"] == job_id
    assert data["status"] == "pending"
    assert data["estimated_wait_time"] == 60
    assert data["created_at"] is not None
    assert data["started_at"] is None
    assert data["completed_at"] is None


def test_get_backtest_quota_returns_plan_snapshot(client, app):
    from app.extensions import db
    from app.models import UserQuota

    token, user_id = _login_user(client, phone="13800138004", nickname="QuotaSnapshot")

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        if quota is None:
            quota = UserQuota(user_id=user_id)
            db.session.add(quota)
        quota.plan_level = "basic"
        quota.used_count = 12
        db.session.commit()

    response = client.get("/api/v1/backtest/quota", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"]["plan_level"] == "basic"
    assert response.json["data"]["plan_limit"] == 100
    assert response.json["data"]["used_count"] == 12
    assert "reset_at" in response.json["data"]


def test_worker_deducts_quota_when_job_starts(monkeypatch, app):
    from app.extensions import db
    from app.models import BacktestJob, Strategy, User, UserQuota
    from app.tasks.backtests import _run_job

    with app.app_context():
        user = User(phone="13800138005", nickname="WorkerUser")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Strategy(
                id="worker-strategy",
                name="Worker Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user.id,
            )
        )
        db.session.add(UserQuota(user_id=user.id, plan_level="free", used_count=0))
        job = BacktestJob(
            user_id=user.id,
            strategy_id="worker-strategy",
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.backtests.run_backtest",
        lambda *args, **kwargs: {"summary": {"totalReturn": 1}},
    )

    result = _run_job(job_id)

    assert result["summary"]["totalReturn"] == 1

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        job = db.session.get(BacktestJob, job_id)
        assert quota.used_count == 1
        assert job.status == "completed"


def test_worker_marks_job_failed_when_quota_is_exhausted(monkeypatch, app):
    from app.extensions import db
    from app.models import BacktestJob, Strategy, User, UserQuota
    from app.tasks.backtests import _run_job

    with app.app_context():
        user = User(phone="13800138006", nickname="NoQuotaUser")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Strategy(
                id="no-quota-strategy",
                name="NoQuota Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user.id,
            )
        )
        db.session.add(UserQuota(user_id=user.id, plan_level="free", used_count=10))
        job = BacktestJob(
            user_id=user.id,
            strategy_id="no-quota-strategy",
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
        user_id = user.id

    called = {"value": False}

    def _fake_run_backtest(*args, **kwargs):
        called["value"] = True
        return {"summary": {"totalReturn": 1}}

    monkeypatch.setattr("app.tasks.backtests.run_backtest", _fake_run_backtest)

    result = _run_job(job_id)

    assert result["status"] == "failed"
    assert called["value"] is False

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        job = db.session.get(BacktestJob, job_id)
        assert quota.used_count == 10
        assert job.status == "failed"
        assert job.error_message == "quota_exceeded"
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
