from app.extensions import db
from app.models import User


def test_user_model_fields(app):
    with app.app_context():
        db.create_all()
        user = User(email='admin@example.com', name='Admin', password_hash='x')
        db.session.add(user)
        db.session.commit()
        assert user.id is not None
