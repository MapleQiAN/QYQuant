
def test_not_found_error_shape(client):
    resp = client.get('/api/does-not-exist')
    assert resp.status_code == 404
    assert resp.json['code'] == 40400
    assert isinstance(resp.json['message'], str)
    assert 'details' in resp.json
