
def test_file_upload_requires_auth(client):
    resp = client.post('/api/files')
    assert resp.status_code == 401
