
def test_forum_hot(client):
    resp = client.get('/api/forum/hot')
    assert resp.status_code == 200
    assert isinstance(resp.json['data'], list)
