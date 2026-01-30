
def test_backtest_run_and_job(client, seed_user):
    resp = client.post('/api/backtests/run', json={"name": "demo", "symbol": "BTCUSDT"})
    assert resp.status_code == 200
    job_id = resp.json['data']['job_id']
    status = client.get(f'/api/backtests/job/{job_id}')
    assert status.status_code == 200
