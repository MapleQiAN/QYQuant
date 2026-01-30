
def test_recent_bots(client):
    resp = client.get('/api/bots/recent')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
