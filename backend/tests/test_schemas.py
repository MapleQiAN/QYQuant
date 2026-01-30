from app.schemas import UserSchema


def test_user_schema_shape():
    data = UserSchema().dump({
        'id': 'u1',
        'name': 'Admin',
        'avatar': 'x',
        'level': 'VIP',
        'notifications': 2,
    })
    assert data['name'] == 'Admin'
