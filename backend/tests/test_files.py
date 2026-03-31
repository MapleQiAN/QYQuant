from io import BytesIO


def _register_and_login(client, email="avatar@example.com", nickname="Avatar User"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Secret123!",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_file_upload_requires_auth(client):
    resp = client.post("/api/files")
    assert resp.status_code == 401


def test_file_upload_accepts_avatar_images_and_returns_public_url(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/files",
        headers=_auth_headers(token),
        data={
            "file": (BytesIO(b"\x89PNG\r\n\x1a\navatar-bytes"), "avatar.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"]
    assert data["url"] == f"/api/files/{data['id']}/content"

    public_response = client.get(data["url"])
    assert public_response.status_code == 200
    assert public_response.headers["Content-Type"] == "image/png"
    assert public_response.data.startswith(b"\x89PNG\r\n\x1a\n")


def test_public_file_content_rejects_non_image_assets(client):
    token = _register_and_login(client, email="code@example.com", nickname="Code User")
    upload_response = client.post(
        "/api/files",
        headers=_auth_headers(token),
        data={
            "file": (BytesIO(b"print('secret')"), "strategy.py"),
        },
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 200
    file_id = upload_response.json["data"]["id"]

    public_response = client.get(f"/api/files/{file_id}/content")
    assert public_response.status_code == 403
