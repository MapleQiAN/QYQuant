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


def _seed_runtime_strategy(app, tmp_path, strategy_id='sandbox-strategy', version='1.0.0', owner_id=None):
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
            owner_id=owner_id,
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


def test_legacy_backtest_run_requires_auth(client):
    response = client.post('/api/backtests/run', json={"symbol": "BTCUSDT"})

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_legacy_backtest_latest_requires_auth(client):
    response = client.get('/api/backtests/latest?symbol=BTCUSDT&limit=10')

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_legacy_backtest_job_requires_auth(client):
    from app.extensions import db
    from app.models import BacktestJob

    token, user_id = _login_user(client, phone="13800138033", nickname="LegacyJobOwner")

    with client.application.app_context():
        job = BacktestJob(user_id=user_id, params={"symbol": "BTCUSDT"})
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    response = client.get(f"/api/backtests/job/{job_id}")

    assert token
    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_legacy_backtest_job_hides_other_users(client, app):
    from app.extensions import db
    from app.models import BacktestJob

    owner_token, owner_id = _login_user(client, phone="13800138034", nickname="LegacyOwner")
    reader_token, reader_id = _login_user(client, phone="13800138035", nickname="LegacyReader")

    with app.app_context():
        job = BacktestJob(user_id=owner_id, params={"symbol": "BTCUSDT"})
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    response = client.get(f"/api/backtests/job/{job_id}", headers=_auth_headers(reader_token))

    assert owner_token != reader_token
    assert owner_id != reader_id
    assert response.status_code == 404


def test_legacy_backtest_run_ignores_payload_user_id(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    token, user_id = _login_user(client, phone="13800138017", nickname="LegacyRunner")
    _, other_user_id = _login_user(client, phone="13800138018", nickname="SpoofTarget")

    monkeypatch.setattr("app.tasks.backtests.run_backtest", lambda *args, **kwargs: {"summary": {"totalReturn": 1}})

    response = client.post(
        '/api/backtests/run',
        headers=_auth_headers(token),
        json={"symbol": "BTCUSDT", "user_id": other_user_id, "userId": other_user_id},
    )

    assert response.status_code == 200
    job_id = response.json["data"]["job_id"]
    assert other_user_id != user_id

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job is not None
        assert job.user_id == user_id


def test_backtest_run_persists_completed_job_and_query_reads_database(client, app):
    from app.extensions import db
    from app.models import BacktestJob

    token, _ = _login_user(client, phone="13800138021", nickname="LegacyPersist")

    resp = client.post(
        '/api/backtests/run',
        headers=_auth_headers(token),
        json={"symbol": "BTCUSDT", "limit": 20},
    )

    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job is not None
        assert job.status == 'completed'
        assert job.params['symbol'] == 'BTCUSDT'
        assert job.result_summary is not None

    status = client.get(f'/api/backtests/job/{job_id}', headers=_auth_headers(token))
    assert status.status_code == 200
    assert status.json['data']['job_id'] == job_id
    assert status.json['data']['status'] == 'completed'
    assert status.json['data']['result_summary'] is not None


def test_backtest_run_marks_failed_jobs(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    token, _ = _login_user(client, phone="13800138022", nickname="LegacyFailure")

    def _raise_failure(*args, **kwargs):
        raise RuntimeError('boom')

    monkeypatch.setattr('app.tasks.backtests.run_backtest', _raise_failure)

    resp = client.post('/api/backtests/run', headers=_auth_headers(token), json={"symbol": "BTCUSDT"})
    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job.status == 'failed'
        assert 'boom' in job.error_message


def test_backtest_run_marks_timeout_jobs(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    token, _ = _login_user(client, phone="13800138023", nickname="LegacyTimeout")

    def _raise_timeout(*args, **kwargs):
        raise SoftTimeLimitExceeded()

    monkeypatch.setattr('app.tasks.backtests.run_backtest', _raise_timeout)

    resp = client.post('/api/backtests/run', headers=_auth_headers(token), json={"symbol": "BTCUSDT"})
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


def test_submit_backtest_persists_custom_name(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob, Strategy, UserQuota

    token, user_id = _login_user(client, phone="13800138014", nickname="NamedSubmitter")

    with app.app_context():
        strategy = Strategy(
            id="named-strategy",
            name="Named Strategy",
            symbol="BTCUSDT",
            status="draft",
            owner_id=user_id,
        )
        db.session.add(strategy)
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "free"
        quota.used_count = 0
        db.session.commit()

    monkeypatch.setattr("app.blueprints.backtests.run_backtest_task.apply_async", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/backtest/",
        headers=_auth_headers(token),
        json={
            "strategy_id": "named-strategy",
            "symbols": ["BTCUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "name": "Trend Follow Jan Run",
        },
    )

    assert response.status_code == 200
    job_id = response.json["data"]["job_id"]

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job is not None
        assert job.params["name"] == "Trend Follow Jan Run"


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


def test_get_backtest_status_returns_structured_error_for_failed_job(client, app):
    import json

    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy

    token, user_id = _login_user(client, phone="13800138013", nickname="StatusErrorUser")

    structured_error = {
        "type": "NameError",
        "line": 15,
        "message": "Undefined variable 'sma_period'",
        "suggestion": "Define sma_period before using it.",
        "example_code": "sma_period = ctx.params.get('sma_period', 20)",
        "raw_error": "NameError: name 'sma_period' is not defined",
    }

    with app.app_context():
        db.session.add(
            Strategy(
                id="status-error-strategy",
                name="Status Error Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        job = BacktestJob(
            user_id=user_id,
            strategy_id="status-error-strategy",
            status=BacktestJobStatus.FAILED.value,
            params={"symbol": "BTCUSDT"},
            error_message=json.dumps(structured_error, ensure_ascii=False),
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    response = client.get(f"/api/v1/backtest/{job_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["job_id"] == job_id
    assert data["status"] == "failed"
    assert data["error"]["type"] == "NameError"
    assert data["error"]["line"] == 15
    assert data["error"]["message"] == "Undefined variable 'sma_period'"


def test_get_backtest_history_returns_named_jobs_for_owner(client, app):
    from datetime import datetime, timedelta, timezone

    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy

    token, user_id = _login_user(client, phone="13800138015", nickname="HistoryOwner")
    _, other_user_id = _login_user(client, phone="13800138016", nickname="HistoryOther")
    base_time = datetime(2026, 4, 8, 10, 0, tzinfo=timezone.utc)

    with app.app_context():
        db.session.add_all(
            [
                Strategy(
                    id="history-strategy-a",
                    name="Trend Alpha",
                    symbol="BTCUSDT",
                    status="draft",
                    owner_id=user_id,
                ),
                Strategy(
                    id="history-strategy-b",
                    name="Mean Reversion",
                    symbol="ETHUSDT",
                    status="draft",
                    owner_id=user_id,
                ),
                Strategy(
                    id="history-hidden-strategy",
                    name="Hidden Strategy",
                    symbol="SOLUSDT",
                    status="draft",
                    owner_id=other_user_id,
                ),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                BacktestJob(
                    user_id=user_id,
                    strategy_id="history-strategy-a",
                    status=BacktestJobStatus.COMPLETED.value,
                    params={
                        "name": "Alpha Breakout April",
                        "symbol": "BTCUSDT",
                        "start_date": "2024-04-01",
                        "end_date": "2024-04-30",
                    },
                    result_summary={"totalReturn": 12.4},
                    created_at=base_time,
                ),
                BacktestJob(
                    user_id=user_id,
                    strategy_id="history-strategy-b",
                    status=BacktestJobStatus.FAILED.value,
                    params={
                        "name": "ETH Mean Reversion Retry",
                        "symbol": "ETHUSDT",
                        "start_date": "2024-03-01",
                        "end_date": "2024-03-31",
                    },
                    error_message="strategy_timeout",
                    created_at=base_time + timedelta(minutes=10),
                ),
                BacktestJob(
                    user_id=other_user_id,
                    strategy_id="history-hidden-strategy",
                    status=BacktestJobStatus.COMPLETED.value,
                    params={"name": "Should Not Be Visible", "symbol": "SOLUSDT"},
                    created_at=base_time + timedelta(minutes=20),
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/backtest/history", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json["data"]["items"]
    assert len(items) == 2
    assert [item["name"] for item in items] == [
        "ETH Mean Reversion Retry",
        "Alpha Breakout April",
    ]
    assert items[0]["strategy_name"] == "Mean Reversion"
    assert items[0]["symbol"] == "ETHUSDT"
    assert items[0]["status"] == "failed"
    assert items[0]["has_report"] is True
    assert items[1]["result_summary"]["totalReturn"] == 12.4


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
    from app.models import BacktestJob, BacktestQuotaLedger, Strategy, User, UserQuota
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

    with app.app_context():
        result = _run_job(job_id)

    assert result["summary"]["totalReturn"] == 1

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        ledger = db.session.get(BacktestQuotaLedger, job_id)
        job = db.session.get(BacktestJob, job_id)
        assert quota.used_count == 1
        assert ledger is not None
        assert ledger.status == "consumed"
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

    with app.app_context():
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


def test_submit_backtest_reserves_quota_by_job_id(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestQuotaLedger, Strategy, UserQuota

    token, user_id = _login_user(client, phone="13800138028", nickname="ReservedQuotaUser")

    with app.app_context():
        db.session.add(
            Strategy(
                id="reserved-quota-strategy",
                name="Reserved Quota Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "free"
        quota.used_count = 0
        db.session.commit()

    monkeypatch.setattr("app.blueprints.backtests.run_backtest_task.apply_async", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/backtest/",
        headers=_auth_headers(token),
        json={
            "strategy_id": "reserved-quota-strategy",
            "symbols": ["BTCUSDT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )

    assert response.status_code == 200
    job_id = response.json["data"]["job_id"]

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        ledger = db.session.get(BacktestQuotaLedger, job_id)
        job = db.session.get(BacktestJob, job_id)
        assert quota.used_count == 1
        assert ledger is not None
        assert ledger.status == "reserved"
        assert job.status == "pending"


def test_worker_releases_quota_when_report_write_fails(monkeypatch, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestQuotaLedger, Strategy, User, UserQuota
    from app.tasks.backtests import _run_job

    with app.app_context():
        user = User(phone="13800138029", nickname="ReleaseQuotaUser")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Strategy(
                id="release-quota-strategy",
                name="Release Quota Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user.id,
            )
        )
        db.session.add(UserQuota(user_id=user.id, plan_level="free", used_count=0))
        job = BacktestJob(
            user_id=user.id,
            strategy_id="release-quota-strategy",
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.backtests.run_backtest",
        lambda *args, **kwargs: {"summary": {"totalReturn": 1}, "kline": [], "trades": []},
    )
    monkeypatch.setattr("app.tasks.backtests.write_json", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("disk full")))

    with app.app_context():
        result = _run_job(job_id)

    assert result["status"] == "failed"

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        ledger = db.session.get(BacktestQuotaLedger, job_id)
        job = db.session.get(BacktestJob, job_id)
        assert quota.used_count == 0
        assert ledger is not None
        assert ledger.status == "released"
        assert job.status == "failed"
        assert "disk full" in job.error_message


def test_worker_duplicate_execution_does_not_double_charge_quota(monkeypatch, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestQuotaLedger, Strategy, User, UserQuota
    from app.tasks.backtests import _run_job

    with app.app_context():
        user = User(phone="13800138030", nickname="DuplicateChargeUser")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Strategy(
                id="duplicate-charge-strategy",
                name="Duplicate Charge Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user.id,
            )
        )
        db.session.add(UserQuota(user_id=user.id, plan_level="free", used_count=0))
        job = BacktestJob(
            user_id=user.id,
            strategy_id="duplicate-charge-strategy",
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.backtests.run_backtest",
        lambda *args, **kwargs: {"summary": {"totalReturn": 1}, "kline": [], "trades": []},
    )

    with app.app_context():
        first = _run_job(job_id)
        second = _run_job(job_id)

    assert first["summary"]["totalReturn"] == 1
    assert second["summary"]["totalReturn"] == 1

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        ledger = db.session.get(BacktestQuotaLedger, job_id)
        assert quota.used_count == 1
        assert ledger is not None
        assert ledger.status == "consumed"


def test_failed_job_does_not_block_later_job(monkeypatch, client, app):
    from app.extensions import db
    from app.models import BacktestJob

    token, _ = _login_user(client, phone="13800138024", nickname="LegacyRetry")
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

    first = client.post('/api/backtests/run', headers=_auth_headers(token), json={"symbol": "BTCUSDT"})
    second = client.post('/api/backtests/run', headers=_auth_headers(token), json={"symbol": "ETHUSDT"})

    with app.app_context():
        failed = db.session.get(BacktestJob, first.json['data']['job_id'])
        completed = db.session.get(BacktestJob, second.json['data']['job_id'])
        assert failed.status == 'failed'
        assert completed.status == 'completed'


def test_backtest_latest_remains_synchronous_debug_endpoint(client):
    token, _ = _login_user(client, phone="13800138025", nickname="LegacyLatest")

    resp = client.get('/api/backtests/latest?symbol=BTCUSDT&limit=10', headers=_auth_headers(token))

    assert resp.status_code == 200
    assert resp.json['data']['summary'] is not None
    assert 'job_id' not in resp.json['data']


def test_backtest_run_executes_strategy_via_sandbox(monkeypatch, client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138026", nickname="SandboxRunner")
    strategy_id, version = _seed_runtime_strategy(app, tmp_path, owner_id=user_id)

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
        headers=_auth_headers(token),
        json={
            "symbol": "BTCUSDT",
            "strategyId": strategy_id,
            "strategyVersion": version,
            "strategyParams": {"window": 5},
        },
    )

    assert response.status_code == 200
    job_id = response.json['data']['job_id']

    status = client.get(f'/api/backtests/job/{job_id}', headers=_auth_headers(token))
    assert status.status_code == 200
    assert status.json['data']['status'] == 'completed'
    assert status.json['data']['result']['runtime']['logs'] == ['sandbox-ok']
    assert status.json['data']['result']['trades'][0]['side'] == 'buy'


def test_backtest_run_marks_strategy_timeout_jobs(monkeypatch, client, app, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob
    from app.strategy_runtime.errors import StrategyRuntimeError

    token, user_id = _login_user(client, phone="13800138027", nickname="SandboxTimeout")
    strategy_id, version = _seed_runtime_strategy(app, tmp_path, strategy_id='timeout-strategy', owner_id=user_id)

    def _raise_timeout(*args, **kwargs):
        raise StrategyRuntimeError('strategy_timeout')

    monkeypatch.setattr('app.services.sandbox.execute_strategy', _raise_timeout)

    response = client.post(
        '/api/backtests/run',
        headers=_auth_headers(token),
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


def _build_report_fixture():
    base_time = 1700000000000
    kline = [
        {
            "time": base_time,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1000,
        },
        {
            "time": base_time + 86_400_000,
            "open": 100.0,
            "high": 108.0,
            "low": 99.0,
            "close": 105.0,
            "volume": 1100,
        },
        {
            "time": base_time + 2 * 86_400_000,
            "open": 105.0,
            "high": 111.0,
            "low": 104.0,
            "close": 110.0,
            "volume": 1200,
        },
        {
            "time": base_time + 3 * 86_400_000,
            "open": 110.0,
            "high": 112.0,
            "low": 107.0,
            "close": 108.0,
            "volume": 1250,
        },
        {
            "time": base_time + 4 * 86_400_000,
            "open": 108.0,
            "high": 109.0,
            "low": 101.0,
            "close": 102.0,
            "volume": 1300,
        },
    ]
    trades = [
        {
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 100.0,
            "quantity": 10.0,
            "timestamp": base_time,
            "pnl": None,
        },
        {
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 110.0,
            "quantity": 10.0,
            "timestamp": base_time + 2 * 86_400_000,
            "pnl": 100.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 108.0,
            "quantity": 5.0,
            "timestamp": base_time + 3 * 86_400_000,
            "pnl": None,
        },
        {
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 102.0,
            "quantity": 5.0,
            "timestamp": base_time + 4 * 86_400_000,
            "pnl": -30.0,
        },
    ]
    return {
        "kline": kline,
        "trades": trades,
        "dataSource": "mock",
    }


def test_worker_generates_report_summary_and_storage_artifacts(monkeypatch, app, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob, Strategy, User, UserQuota
    from app.tasks.backtests import _run_job

    storage_dir = tmp_path / "storage"
    monkeypatch.setenv("BACKTEST_STORAGE_DIR", storage_dir.as_posix())

    with app.app_context():
        user = User(phone="13800138007", nickname="ReportOwner")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Strategy(
                id="report-strategy",
                name="Report Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user.id,
            )
        )
        db.session.add(UserQuota(user_id=user.id, plan_level="free", used_count=0))
        job = BacktestJob(
            user_id=user.id,
            strategy_id="report-strategy",
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    monkeypatch.setattr("app.tasks.backtests.run_backtest", lambda *args, **kwargs: _build_report_fixture())

    with app.app_context():
        _run_job(job_id)

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        assert job.status == "completed"
        assert job.result_storage_key == f"backtest-results/{job_id}"
        assert job.result_summary is not None
        assert {
            "totalReturn",
            "annualizedReturn",
            "maxDrawdown",
            "sharpeRatio",
            "volatility",
            "sortinoRatio",
            "calmarRatio",
            "winRate",
            "profitLossRatio",
            "maxConsecutiveLosses",
            "totalTrades",
        }.issubset(set(job.result_summary.keys()))

    assert (storage_dir / "backtest-results" / job_id / "equity_curve.json").exists()
    assert (storage_dir / "backtest-results" / job_id / "trades.json").exists()


def test_get_backtest_report_returns_saved_artifacts_for_owner(client, app, tmp_path, monkeypatch):
    import json

    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy

    storage_dir = tmp_path / "storage"
    monkeypatch.setenv("BACKTEST_STORAGE_DIR", storage_dir.as_posix())

    token, user_id = _login_user(client, phone="13800138008", nickname="ReportReader")

    with app.app_context():
        db.session.add(
            Strategy(
                id="report-reader-strategy",
                name="Reader Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        job = BacktestJob(
            user_id=user_id,
            strategy_id="report-reader-strategy",
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_summary={"totalReturn": 7.5, "maxDrawdown": -2.0, "sharpeRatio": 1.2},
            result_storage_key="backtest-results/report-job",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    storage_root = storage_dir / "backtest-results" / "report-job"
    storage_root.mkdir(parents=True)
    (storage_root / "equity_curve.json").write_text(
        json.dumps([{"timestamp": 1700000000000, "equity": 100000.0}], ensure_ascii=False),
        encoding="utf-8",
    )
    (storage_root / "trades.json").write_text(
        json.dumps(
            [{"symbol": "BTCUSDT", "side": "buy", "price": 100.0, "quantity": 1.0, "timestamp": 1700000000000}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (storage_root / "kline.json").write_text(
        json.dumps(
            [{"time": 1700000000000, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    response = client.get(f"/api/v1/backtest/{job_id}/report", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["result_summary"]["totalReturn"] == 7.5
    assert data["equity_curve"][0]["equity"] == 100000.0
    assert data["trades"][0]["side"] == "buy"


def test_get_backtest_report_hides_non_owner_jobs(client, app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", (tmp_path / "storage").as_posix())

    owner_token, owner_id = _login_user(client, phone="13800138009", nickname="Owner")
    reader_token, reader_id = _login_user(client, phone="13800138010", nickname="Reader")

    with app.app_context():
        db.session.add(
            Strategy(
                id="hidden-report-strategy",
                name="Hidden Report Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=owner_id,
            )
        )
        job = BacktestJob(
            user_id=owner_id,
            strategy_id="hidden-report-strategy",
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_summary={"totalReturn": 1.0},
            result_storage_key="backtest-results/hidden-job",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    assert owner_token != reader_token
    assert owner_id != reader_id

    response = client.get(f"/api/v1/backtest/{job_id}/report", headers=_auth_headers(reader_token))

    assert response.status_code == 404
    assert response.json["error"]["code"] == "JOB_NOT_FOUND"


def test_get_backtest_report_returns_structured_error_for_failed_job(client, app):
    import json

    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, Strategy

    token, user_id = _login_user(client, phone="13800138011", nickname="FailedReader")

    structured_error = {
        "type": "NameError",
        "line": 15,
        "message": "未定义的变量 'sma_period'",
        "suggestion": "请检查变量名是否正确，或确认是否已在策略参数中定义该参数",
        "example_code": "sma_period = ctx.params.get('sma_period', 20)",
        "raw_error": "NameError: name 'sma_period' is not defined",
    }

    with app.app_context():
        db.session.add(
            Strategy(
                id="failed-report-strategy",
                name="Failed Report Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=user_id,
            )
        )
        job = BacktestJob(
            user_id=user_id,
            strategy_id="failed-report-strategy",
            status=BacktestJobStatus.FAILED.value,
            params={"symbol": "BTCUSDT"},
            error_message=json.dumps(structured_error, ensure_ascii=False),
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    response = client.get(f"/api/v1/backtest/{job_id}/report", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["job_id"] == job_id
    assert data["status"] == "failed"
    assert data["error"]["type"] == "NameError"
    assert data["error"]["line"] == 15
    assert "sma_period" in data["error"]["message"]
    assert "ctx.params" in data["error"]["example_code"]


def test_get_supported_packages_returns_whitelist(client):
    token, _ = _login_user(client, phone="13800138012", nickname="PackageReader")

    response = client.get("/api/v1/backtest/supported-packages", headers=_auth_headers(token))

    assert response.status_code == 200
    packages = response.json["data"]["packages"]
    assert any(item["name"] == "pandas" for item in packages)
    assert any(item["name"] == "numpy" for item in packages)
    assert any(item["name"] == "ta-lib" for item in packages)
    pandas = next(item for item in packages if item["name"] == "pandas")
    assert pandas["version"]
    assert pandas["description"]


def test_worker_persists_structured_error_payload(monkeypatch, client, app):
    import json

    from app.extensions import db
    from app.models import BacktestJob
    from app.strategy_runtime.errors import StrategyRuntimeError

    def _raise_runtime_error(*args, **kwargs):
        raise StrategyRuntimeError(
            "strategy_runtime_error",
            {
                "reason": """
Traceback (most recent call last):
  File "/sandbox/workdir/strategy.py", line 21, in <module>
    result = missing_factor * close
NameError: name 'missing_factor' is not defined
""".strip()
            },
        )

    monkeypatch.setattr("app.tasks.backtests.run_backtest", _raise_runtime_error)

    token, _ = _login_user(client, phone="13800138028", nickname="LegacyStructuredError")

    response = client.post("/api/backtests/run", headers=_auth_headers(token), json={"symbol": "BTCUSDT"})
    assert response.status_code == 200
    job_id = response.json["data"]["job_id"]

    with app.app_context():
        job = db.session.get(BacktestJob, job_id)
        payload = json.loads(job.error_message)
        assert job.status == "failed"
        assert payload["type"] == "NameError"
        assert payload["line"] == 21
        assert "missing_factor" in payload["message"]
