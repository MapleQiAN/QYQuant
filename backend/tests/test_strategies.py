
def test_recent_strategies(client):
    resp = client.get('/api/strategies/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
