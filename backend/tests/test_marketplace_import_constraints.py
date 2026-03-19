import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Strategy, User


def test_strategy_import_source_constraint_prevents_duplicate_marketplace_imports(app):
    with app.app_context():
        user = User(phone="13800138999", nickname="ConstraintUser")
        source_strategy = Strategy(
            id="source-marketplace-strategy",
            name="Source Strategy",
            title="Source Strategy",
            symbol="XAUUSD",
            status="completed",
            owner_id=None,
            source="marketplace",
            is_public=True,
            review_status="approved",
        )
        db.session.add_all([user, source_strategy])
        db.session.flush()

        db.session.add(
            Strategy(
                id="user-import-1",
                name="Imported Strategy 1",
                symbol="XAUUSD",
                status="draft",
                owner_id=user.id,
                source="marketplace",
                source_strategy_id=source_strategy.id,
            )
        )
        db.session.commit()

        db.session.add(
            Strategy(
                id="user-import-2",
                name="Imported Strategy 2",
                symbol="XAUUSD",
                status="draft",
                owner_id=user.id,
                source="marketplace",
                source_strategy_id=source_strategy.id,
            )
        )

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
