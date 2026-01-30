
def test_login_and_me(client, seed_user):
    resp = client.post('/api/auth/login', json={"email": "admin@example.com", "password": "admin123"})
    assert resp.status_code == 200
    token = resp.json['data']['access_token']
    assert isinstance(token, str)

    me = client.get('/api/users/me', headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json['data']['email'] == 'admin@example.com'
