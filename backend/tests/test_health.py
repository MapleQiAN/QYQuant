
def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json['code'] == 0
    assert resp.json['data']['status'] == 'ok'
    assert isinstance(resp.json.get('request_id'), str)
