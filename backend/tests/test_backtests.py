from celery.exceptions import SoftTimeLimitExceeded


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
