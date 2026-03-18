import json
import uuid

from app.extensions import db
from app.models import BacktestJob, BacktestJobStatus, Strategy, User


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138100", nickname="MarketplaceUser"):
    _seed_code(client.application, phone)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_marketplace_strategy(app, tmp_path):
    strategy_id = "public-marketplace-strategy"

    with app.app_context():
        author = User(
            id="marketplace-author",
            phone="13800138101",
            nickname="QuantAlice",
            avatar_url="https://example.com/avatar.png",
            bio="quant developer",
        )
        db.session.add(author)

        strategy = Strategy(
            id=strategy_id,
            name="Golden Breakout",
            symbol="XAUUSD",
            status="completed",
            description="Trend-following breakout strategy for gold.",
            category="trend-following",
            source="marketplace",
            tags=["gold", "breakout"],
            owner_id=author.id,
            code_hash="marketplace-strategy-hash",
            created_at=1700000000000,
            is_public=True,
            is_verified=True,
            review_status="approved",
            display_metrics={
                "totalReturn": 18.6,
                "maxDrawdown": -6.2,
                "sharpeRatio": 1.54,
                "winRate": 62.0,
            },
        )
        db.session.add(strategy)

        job = BacktestJob(
            id="marketplace-job",
            strategy_id=strategy.id,
            status=BacktestJobStatus.COMPLETED.value,
            result_summary={"totalReturn": 18.6},
            result_storage_key="backtest-results/marketplace-job",
        )
        db.session.add(job)
        db.session.commit()

    storage_root = tmp_path / "storage" / "backtest-results" / "marketplace-job"
    storage_root.mkdir(parents=True)
    (storage_root / "equity_curve.json").write_text(
        json.dumps(
            [
                {"timestamp": 1700000000000, "equity": 100000.0, "benchmark_equity": 100000.0},
                {"timestamp": 1700086400000, "equity": 101250.5, "benchmark_equity": 100800.0},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return strategy_id


def test_get_marketplace_strategy_detail_returns_public_fields_and_hides_code(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}")

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == strategy_id
    assert data["title"] == "Golden Breakout"
    assert data["description"] == "Trend-following breakout strategy for gold."
    assert data["category"] == "trend-following"
    assert data["tags"] == ["gold", "breakout"]
    assert data["is_verified"] is True
    assert data["display_metrics"]["sharpeRatio"] == 1.54
    assert data["author"] == {
        "nickname": "QuantAlice",
        "avatar_url": "https://example.com/avatar.png",
    }
    assert data["created_at"].endswith("+08:00")
    assert "code_encrypted" not in data
    assert "code_hash" not in data
    assert "result_storage_key" not in data


def test_get_marketplace_strategy_detail_returns_imported_state_for_authenticated_user(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138102", nickname="Importer")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        imported_strategy = Strategy(
            id=f"imported-{uuid.uuid4().hex[:8]}",
            name="Imported Golden Breakout",
            symbol="XAUUSD",
            status="draft",
            owner_id=user_id,
            code_hash="marketplace-strategy-hash",
            source="upload",
        )
        db.session.add(imported_strategy)
        db.session.commit()
        imported_strategy_id = imported_strategy.id

    response = client.get(
        f"/api/v1/marketplace/strategies/{strategy_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"]["already_imported"] is True
    assert response.json["data"]["imported_strategy_id"] == imported_strategy_id


def test_get_marketplace_strategy_detail_returns_404_for_non_public_strategy(client, app):
    with app.app_context():
        strategy = Strategy(
            id="private-marketplace-strategy",
            name="Private Strategy",
            symbol="BTCUSDT",
            status="draft",
            is_public=False,
            review_status="pending",
        )
        db.session.add(strategy)
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies/private-marketplace-strategy")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "STRATEGY_NOT_FOUND"


def test_get_marketplace_equity_curve_returns_dates_and_values(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}/equity-curve")

    assert response.status_code == 200
    assert response.json["data"] == {
        "dates": [1700000000000, 1700086400000],
        "values": [100000.0, 101250.5],
    }
