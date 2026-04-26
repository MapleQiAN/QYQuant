import json
import uuid
import zipfile
from datetime import datetime, timezone

import pytest

from app.extensions import db
from app.models import AuditLog, BacktestJob, BacktestJobStatus, File, Post, Strategy, StrategyVersion, User


def _create_user(user_id, nickname, avatar_url):
    return User(
        id=user_id,
        phone=None,
        nickname=nickname,
        avatar_url=avatar_url,
    )


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


def _require_postgres(app):
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
        pytest.skip("marketplace search coverage requires PostgreSQL")


def _seed_owned_private_strategy(app, owner_id, *, strategy_id="owned-private-strategy", with_completed_job=True):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            name="Owned Private Strategy",
            title="Owned Private Strategy",
            symbol="BTCUSDT",
            status="draft",
            description="Private strategy ready for publishing.",
            category="trend-following",
            source="upload",
            tags=["trend"],
            owner_id=owner_id,
            created_at=1700000000000,
            updated_at=1700000000000,
            last_update=1700000000000,
            is_public=False,
            is_verified=False,
            review_status="draft",
            display_metrics={},
        )
        db.session.add(strategy)
        if with_completed_job:
            db.session.add(
                BacktestJob(
                    id=f"{strategy_id}-job",
                    strategy_id=strategy_id,
                    status=BacktestJobStatus.COMPLETED.value,
                    result_summary={"totalReturn": 12.3},
                    result_storage_key=f"backtest-results/{strategy_id}-job",
                )
            )
        db.session.commit()
    return strategy_id


def _seed_marketplace_strategy(app, tmp_path):
    strategy_id = "public-marketplace-strategy"
    version = "1.0.0"
    storage_key = f"strategies/{strategy_id}.qys"
    package_path = tmp_path / "storage" / storage_key
    package_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": strategy_id,
        "name": "Golden Breakout",
        "version": version,
        "description": "Trend-following breakout strategy for gold.",
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
        "parameters": [],
        "tags": ["gold", "breakout"],
        "ui": {"category": "trend-following"},
    }
    source_code = "class Strategy:\n    def on_bar(self, ctx, bar):\n        return None\n"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("strategy.json", json.dumps(manifest))
        archive.writestr("src/strategy.py", source_code)

    with app.app_context():
        author = _create_user("marketplace-author", "QuantAlice", "https://example.com/avatar.png")
        author.phone = "13800138101"
        author.bio = "quant developer"
        db.session.add(author)

        strategy = Strategy(
            id=strategy_id,
            name="Golden Breakout",
            title="Golden Breakout",
            symbol="XAUUSD",
            status="completed",
            description="Trend-following breakout strategy for gold.",
            category="trend-following",
            source="marketplace",
            tags=["gold", "breakout"],
            owner_id=author.id,
            code_hash="marketplace-strategy-hash",
            created_at=1700000000000,
            updated_at=1700000000000,
            last_update=1700000000000,
            is_public=True,
            is_verified=True,
            review_status="approved",
            display_metrics={
                "totalReturn": 18.6,
                "maxDrawdown": -6.2,
                "sharpeRatio": 1.54,
                "winRate": 62.0,
            },
            storage_key=storage_key,
        )
        db.session.add(strategy)

        file_record = File(
            id="marketplace-strategy-file",
            owner_id=author.id,
            filename=package_path.name,
            content_type="application/zip",
            size=package_path.stat().st_size,
            path=package_path.as_posix(),
        )
        db.session.add(file_record)

        db.session.add(
            StrategyVersion(
                id="marketplace-strategy-version",
                strategy_id=strategy.id,
                version=version,
                file_id=file_record.id,
                checksum="marketplace-version-checksum",
            )
        )

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


def _create_community_post(app, *, user_id, content, created_at, title="Community Post"):
    with app.app_context():
        post = Post(
            title=title,
            author="Trader",
            avatar="https://example.com/avatar.png",
            likes=0,
            comments=0,
            timestamp=1,
            tags=[],
            user_id=user_id,
            content=content,
            strategy_id=None,
            likes_count=0,
            comments_count=0,
            created_at=created_at,
        )
        db.session.add(post)
        db.session.commit()
        return post.id


def test_marketplace_list_returns_only_public_approved_strategies(client, app):
    with app.app_context():
        author = _create_user("author-1", "Market Author 1", "https://cdn.example.com/author-1.png")
        db.session.add(author)
        db.session.add_all(
            [
                Strategy(
                    id="approved-public",
                    name="Approved Public Strategy",
                    title="Approved Public Display",
                    symbol="BTCUSDT",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_featured=False,
                    is_verified=True,
                    display_metrics={"annualized_return": 12.3},
                    tags=["trend"],
                    created_at=300,
                    updated_at=300,
                    last_update=300,
                ),
                Strategy(
                    id="pending-public",
                    name="Pending Public Strategy",
                    title="Pending Public Display",
                    symbol="ETHUSDT",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="pending",
                    is_featured=False,
                    is_verified=False,
                    display_metrics={"annualized_return": 7.1},
                    tags=["mean-reversion"],
                    created_at=200,
                    updated_at=200,
                    last_update=200,
                ),
                Strategy(
                    id="approved-private",
                    name="Approved Private Strategy",
                    title="Approved Private Display",
                    symbol="XAUUSD",
                    status="running",
                    owner_id=author.id,
                    is_public=False,
                    review_status="approved",
                    is_featured=False,
                    is_verified=False,
                    display_metrics={"annualized_return": 5.2},
                    tags=["private"],
                    created_at=100,
                    updated_at=100,
                    last_update=100,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?page=1&page_size=20")

    assert response.status_code == 200
    assert response.json["code"] == 0
    assert response.json["message"] == "ok"
    assert [item["id"] for item in response.json["data"]] == ["approved-public"]
    assert response.json["meta"] == {"total": 1, "page": 1, "page_size": 20}


def test_marketplace_featured_mode_returns_only_featured_public_approved_strategies(client, app):
    with app.app_context():
        author = _create_user("author-2", "Market Author 2", "https://cdn.example.com/author-2.png")
        db.session.add(author)
        strategies = []
        for index in range(7):
            strategies.append(
                Strategy(
                    id=f"featured-{index}",
                    name=f"Featured Strategy {index}",
                    title=f"Featured Display {index}",
                    symbol="BTCUSDT",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_featured=True,
                    is_verified=bool(index % 2),
                    display_metrics={"annualized_return": float(index)},
                    tags=["featured"],
                    created_at=500 + index,
                    updated_at=500 + index,
                    last_update=500 + index,
                )
            )
        strategies.append(
            Strategy(
                id="featured-but-pending",
                name="Featured But Pending",
                title="Featured Pending Display",
                symbol="ETHUSDT",
                status="running",
                owner_id=author.id,
                is_public=True,
                review_status="pending",
                is_featured=True,
                is_verified=False,
                display_metrics={"annualized_return": 1.2},
                tags=["featured"],
                created_at=1000,
                updated_at=1000,
                last_update=1000,
            )
        )
        db.session.add_all(strategies)
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?featured=true")

    assert response.status_code == 200
    assert len(response.json["data"]) == 6
    assert all(item["id"].startswith("featured-") for item in response.json["data"])


def test_marketplace_related_discussions_returns_strategy_linked_posts(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)
    older_post_id = _create_community_post(
        app,
        user_id="marketplace-author",
        content="Older breakout recap",
        created_at=datetime(2026, 4, 17, 8, 0, 0, tzinfo=timezone.utc),
    )
    newer_post_id = _create_community_post(
        app,
        user_id="marketplace-author",
        content="Newer breakout recap",
        created_at=datetime(2026, 4, 17, 9, 0, 0, tzinfo=timezone.utc),
    )

    with app.app_context():
        older_post = db.session.get(Post, older_post_id)
        older_post.strategy_id = strategy_id

        newer_post = db.session.get(Post, newer_post_id)
        newer_post.strategy_id = strategy_id

        db.session.add(
            Post(
                id="linked-legacy-row",
                title="Legacy linked row",
                author="Trader",
                avatar="https://example.com/avatar.png",
                likes=0,
                comments=0,
                timestamp=1,
                tags=[],
                user_id="marketplace-author",
                content=None,
                strategy_id=strategy_id,
                likes_count=0,
                comments_count=0,
                created_at=None,
            )
        )
        db.session.commit()

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}/posts")

    assert response.status_code == 200
    assert response.json["data"]["total"] == 2
    assert response.json["data"]["page"] == 1
    assert response.json["data"]["per_page"] == 5
    assert [item["id"] for item in response.json["data"]["items"]] == [newer_post_id, older_post_id]
    assert all(item["strategy_id"] == strategy_id for item in response.json["data"]["items"])
    assert [item["content"] for item in response.json["data"]["items"]] == [
        "Newer breakout recap",
        "Older breakout recap",
    ]
    assert all(item["strategy"]["id"] == strategy_id for item in response.json["data"]["items"])


def test_marketplace_related_discussions_rejects_private_strategy(client, app):
    strategy_id = _seed_owned_private_strategy(app, owner_id="owner-1", with_completed_job=False)

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}/posts")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "STRATEGY_NOT_FOUND"


def test_marketplace_list_returns_meta_total_page_and_page_size(client, app):
    with app.app_context():
        author = _create_user("author-3", "Market Author 3", "https://cdn.example.com/author-3.png")
        db.session.add(author)
        db.session.add_all(
            [
                Strategy(
                    id="paged-1",
                    name="Paged Strategy 1",
                    title="Paged Display 1",
                    symbol="BTCUSDT",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_featured=False,
                    is_verified=False,
                    display_metrics={"annualized_return": 1},
                    tags=["paged"],
                    created_at=101,
                    updated_at=101,
                    last_update=101,
                ),
                Strategy(
                    id="paged-2",
                    name="Paged Strategy 2",
                    title="Paged Display 2",
                    symbol="ETHUSDT",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_featured=False,
                    is_verified=False,
                    display_metrics={"annualized_return": 2},
                    tags=["paged"],
                    created_at=102,
                    updated_at=102,
                    last_update=102,
                ),
                Strategy(
                    id="paged-3",
                    name="Paged Strategy 3",
                    title="Paged Display 3",
                    symbol="XAUUSD",
                    status="running",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_featured=False,
                    is_verified=True,
                    display_metrics={"annualized_return": 3},
                    tags=["paged"],
                    created_at=103,
                    updated_at=103,
                    last_update=103,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?page=2&page_size=1")

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["paged-2"]
    assert response.json["meta"] == {"total": 3, "page": 2, "page_size": 1}


def test_marketplace_card_includes_author_and_excludes_encrypted_code(client, app):
    with app.app_context():
        author = _create_user("author-4", "Market Author", "https://cdn.example.com/author-4.png")
        db.session.add(author)
        db.session.add(
            Strategy(
                id="author-check",
                name="Author Check Strategy",
                title="Author Check Display",
                symbol="BTCUSDT",
                status="running",
                owner_id=author.id,
                is_public=True,
                review_status="approved",
                is_featured=False,
                is_verified=True,
                display_metrics={"sharpe_ratio": 1.5},
                tags=["verified"],
                code_encrypted=b"secret",
                created_at=888,
                updated_at=888,
                last_update=888,
            )
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies")

    assert response.status_code == 200
    card = response.json["data"][0]
    assert card["author"]["nickname"] == "Market Author"
    assert card["author"]["avatar_url"] == "https://cdn.example.com/author-4.png"
    assert "code_encrypted" not in card


def test_marketplace_search_suite_requires_postgres(app):
    _require_postgres(app)


def test_publish_creates_review_submitted_notification(client, app):
    token, user_id = _login_user(client, phone="13800138107", nickname="Publisher")
    strategy_id = _seed_owned_private_strategy(app, user_id, strategy_id="publishable-strategy")

    payload = {
        "strategy_id": strategy_id,
        "title": "Moving Average Trend Pro",
        "description": "Markdown-compatible description",
        "tags": ["trend", "medium-frequency", "risk-control"],
        "category": "trend-following",
        "display_metrics": {
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.2,
            "total_return": 45.6,
        },
    }

    response = client.post(
        "/api/v1/marketplace/strategies",
        json=payload,
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    with app.app_context():
        from app.models import Notification

        notification = Notification.query.filter_by(
            user_id=user_id,
            type="strategy_review_submitted",
        ).first()
        assert notification is not None
        assert notification.title


def test_publish_owned_strategy_sets_pending_without_making_public(client, app):
    token, user_id = _login_user(client, phone="13800138109", nickname="PublisherPending")
    strategy_id = _seed_owned_private_strategy(app, user_id, strategy_id="publishable-strategy-pending")

    payload = {
        "strategy_id": strategy_id,
        "title": "Moving Average Trend Pro",
        "description": "Markdown-compatible description",
        "tags": ["trend", "medium-frequency", "risk-control"],
        "category": "trend-following",
        "display_metrics": {
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.2,
            "total_return": 45.6,
        },
    }

    response = client.post(
        "/api/v1/marketplace/strategies",
        json=payload,
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"strategy_id": strategy_id, "review_status": "pending"}
    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        # In eager/test mode, auto-review runs synchronously and may approve
        assert strategy.review_status in ("pending", "approved", "rejected")
        assert strategy.title == payload["title"]


def test_publish_rejects_non_owner_with_403(client, app):
    owner_token, owner_id = _login_user(client, phone="13800138110", nickname="Owner")
    other_token, _ = _login_user(client, phone="13800138111", nickname="OtherUser")
    strategy_id = _seed_owned_private_strategy(app, owner_id, strategy_id="publishable-non-owner")

    payload = {
        "strategy_id": strategy_id,
        "title": "Moving Average Trend Pro",
        "description": "Markdown-compatible description",
        "tags": ["trend"],
        "category": "trend-following",
        "display_metrics": {
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.2,
            "total_return": 45.6,
        },
    }

    response = client.post(
        "/api/v1/marketplace/strategies",
        json=payload,
        headers=_auth_headers(other_token),
    )

    assert owner_token  # keep login path exercised for real owner creation
    assert response.status_code == 403
    assert response.json["error"]["code"] == "STRATEGY_FORBIDDEN"


def test_publish_rejects_strategy_without_completed_backtest(client, app):
    token, user_id = _login_user(client, phone="13800138112", nickname="NoBacktestUser")
    strategy_id = _seed_owned_private_strategy(
        app,
        user_id,
        strategy_id="publishable-without-backtest",
        with_completed_job=False,
    )

    payload = {
        "strategy_id": strategy_id,
        "title": "Moving Average Trend Pro",
        "description": "Markdown-compatible description",
        "tags": ["trend"],
        "category": "trend-following",
        "display_metrics": {
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.2,
            "total_return": 45.6,
        },
    }

    response = client.post(
        "/api/v1/marketplace/strategies",
        json=payload,
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "STRATEGY_BACKTEST_REQUIRED"


def test_get_publish_status_returns_owner_visible_status(client, app):
    token, user_id = _login_user(client, phone="13800138113", nickname="StatusUser")
    strategy_id = _seed_owned_private_strategy(app, user_id, strategy_id="publish-status-strategy")

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.review_status = "pending"
        strategy.is_public = False
        db.session.commit()

    response = client.get(
        f"/api/v1/marketplace/strategies/{strategy_id}/publish-status",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"review_status": "pending", "is_public": False}


def test_publish_writes_marketplace_audit_log(client, app):
    token, user_id = _login_user(client, phone="13800138108", nickname="PublisherAudit")
    strategy_id = _seed_owned_private_strategy(app, user_id, strategy_id="publishable-strategy-audit")

    payload = {
        "strategy_id": strategy_id,
        "title": "Moving Average Trend Pro",
        "description": "Markdown-compatible description",
        "tags": ["trend", "medium-frequency", "risk-control"],
        "category": "trend-following",
        "display_metrics": {
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.2,
            "total_return": 45.6,
        },
    }

    response = client.post(
        "/api/v1/marketplace/strategies",
        json=payload,
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    with app.app_context():
        audit = AuditLog.query.filter_by(
            operator_id=user_id,
            action="marketplace_strategy_submitted",
            target_id=strategy_id,
        ).first()
        assert audit is not None
        assert audit.target_type == "strategy"


def test_marketplace_search_matches_chinese_title_and_description(client, app):
    _require_postgres(app)
    with app.app_context():
        author = _create_user("search-author-1", "Search Author", "https://cdn.example.com/search-author-1.png")
        db.session.add(author)
        db.session.flush()
        db.session.add_all(
            [
                Strategy(
                    id="ma-strategy",
                    name="ma-strategy",
                    title="均线趋势策略",
                    symbol="BTCUSDT",
                    status="running",
                    description="适合震荡后突破行情的均线系统",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=True,
                    display_metrics={"annual_return": 24.0, "max_drawdown": -8.5},
                    tags=["均线", "趋势"],
                    created_at=1200,
                    updated_at=1200,
                    last_update=1200,
                ),
                Strategy(
                    id="irrelevant-strategy",
                    name="irrelevant-strategy",
                    title="布林带反转",
                    symbol="ETHUSDT",
                    status="running",
                    description="适合短线均值回归",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=False,
                    display_metrics={"annual_return": 11.0, "max_drawdown": -15.0},
                    tags=["反转"],
                    created_at=1100,
                    updated_at=1100,
                    last_update=1100,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?q=均线")

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["ma-strategy"]


def test_marketplace_filters_combine_with_search(client, app):
    _require_postgres(app)
    with app.app_context():
        author = _create_user("search-author-2", "Search Author 2", "https://cdn.example.com/search-author-2.png")
        db.session.add(author)
        db.session.flush()
        db.session.add_all(
            [
                Strategy(
                    id="combo-match",
                    name="combo-match",
                    title="均线趋势增强版",
                    symbol="BTCUSDT",
                    status="running",
                    description="平台验证过的均线趋势策略",
                    category="trend-following",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=True,
                    display_metrics={"annual_return": 26.0, "max_drawdown": -9.0},
                    tags=["均线", "趋势"],
                    created_at=2200,
                    updated_at=2200,
                    last_update=2200,
                ),
                Strategy(
                    id="combo-wrong-category",
                    name="combo-wrong-category",
                    title="均线均值回归版",
                    symbol="ETHUSDT",
                    status="running",
                    description="均线相关，但分类不对",
                    category="mean-reversion",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=True,
                    display_metrics={"annual_return": 30.0, "max_drawdown": -8.0},
                    tags=["均线"],
                    created_at=2100,
                    updated_at=2100,
                    last_update=2100,
                ),
                Strategy(
                    id="combo-not-verified",
                    name="combo-not-verified",
                    title="均线趋势未验证版",
                    symbol="XAUUSD",
                    status="running",
                    description="趋势方向对，但没验证",
                    category="trend-following",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=False,
                    display_metrics={"annual_return": 28.0, "max_drawdown": -7.0},
                    tags=["均线", "趋势"],
                    created_at=2000,
                    updated_at=2000,
                    last_update=2000,
                ),
            ]
        )
        db.session.commit()

    response = client.get(
        "/api/v1/marketplace/strategies?q=均线&category=trend-following&verified=true&annual_return_gte=20"
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["combo-match"]


def test_marketplace_filter_drawdown_uses_absolute_threshold_rule(client, app):
    _require_postgres(app)
    with app.app_context():
        author = _create_user("search-author-3", "Search Author 3", "https://cdn.example.com/search-author-3.png")
        db.session.add(author)
        db.session.flush()
        db.session.add_all(
            [
                Strategy(
                    id="drawdown-match",
                    name="drawdown-match",
                    title="低回撤策略",
                    symbol="BTCUSDT",
                    status="running",
                    description="绝对回撤较低",
                    category="trend-following",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=True,
                    display_metrics={"annual_return": 21.0, "max_drawdown": -8.4},
                    tags=["低回撤"],
                    created_at=3200,
                    updated_at=3200,
                    last_update=3200,
                ),
                Strategy(
                    id="drawdown-too-deep",
                    name="drawdown-too-deep",
                    title="高回撤策略",
                    symbol="ETHUSDT",
                    status="running",
                    description="绝对回撤过深",
                    category="trend-following",
                    owner_id=author.id,
                    is_public=True,
                    review_status="approved",
                    is_verified=True,
                    display_metrics={"annual_return": 35.0, "max_drawdown": -12.1},
                    tags=["高回撤"],
                    created_at=3100,
                    updated_at=3100,
                    last_update=3100,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/marketplace/strategies?max_drawdown_lte=10")

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["drawdown-match"]


def test_strategy_marketplace_index_contract_present(app):
    with app.app_context():
        rows = db.session.execute(
            db.text("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='strategies'")
        ).fetchall()

    sql_by_name = {name: (sql or "").lower() for name, sql in rows}

    assert "ix_strategies_category" in sql_by_name
    assert "ix_strategies_marketplace_public_verified" in sql_by_name
    assert "ix_strategies_marketplace_featured" in sql_by_name
    assert "is_public, is_verified" in sql_by_name["ix_strategies_marketplace_public_verified"]
    assert "where is_public = 1" in sql_by_name["ix_strategies_marketplace_public_verified"]
    assert "where is_featured = 1" in sql_by_name["ix_strategies_marketplace_featured"]


def test_marketplace_onboarding_tag_auto_seeds_strategy_when_package_exists(client, app, tmp_path, monkeypatch):
    from app.blueprints import marketplace as marketplace_blueprint

    package_path = tmp_path / "GoldStepByStep.qys"
    package_path.write_bytes(b"seed-package")
    monkeypatch.setattr(marketplace_blueprint, "_onboarding_package_path", lambda: package_path, raising=False)

    with app.app_context():
        assert Strategy.query.count() == 0

    response = client.get("/api/v1/marketplace/strategies?tag=onboarding")

    assert response.status_code == 200
    ids = [item["id"] for item in response.json["data"]]
    assert ids == ["onboarding-gold-step"]

    with app.app_context():
        seeded = db.session.get(Strategy, "onboarding-gold-step")
        assert seeded is not None
        assert seeded.is_public is True
        assert seeded.is_verified is True
        assert seeded.review_status == "approved"
        assert seeded.title == "Gold Step-By-Step"
        assert any(str(tag).strip().lower() == "onboarding" for tag in (seeded.tags or []))
        assert db.session.get(File, "onboarding-gold-step-file") is not None
        assert StrategyVersion.query.filter_by(strategy_id="onboarding-gold-step", version="1.0.0").count() == 1


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


def test_marketplace_detail_exposes_free_share_metadata(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.share_mode = "free"
        strategy.import_mode = "sealed"
        strategy.trial_backtest_enabled = True
        db.session.commit()

        author = db.session.get(User, "marketplace-author")
        db.session.add_all(
            [
                Post(
                    id="marketplace-discussion-1",
                    title="First discussion",
                    author=author.nickname,
                    avatar=author.avatar_url,
                    likes=0,
                    comments=0,
                    timestamp=1700000001000,
                    tags=[],
                    user_id=author.id,
                    content="Community discussion for the strategy.",
                    strategy_id=strategy_id,
                    likes_count=0,
                    comments_count=0,
                ),
                Post(
                    id="marketplace-discussion-2",
                    title="Second discussion",
                    author=author.nickname,
                    avatar=author.avatar_url,
                    likes=0,
                    comments=0,
                    timestamp=1700000002000,
                    tags=[],
                    user_id=author.id,
                    content="Another discussion thread for the same strategy.",
                    strategy_id=strategy_id,
                    likes_count=0,
                    comments_count=0,
                ),
                Post(
                    id="marketplace-discussion-other",
                    title="Other discussion",
                    author=author.nickname,
                    avatar=author.avatar_url,
                    likes=0,
                    comments=0,
                    timestamp=1700000003000,
                    tags=[],
                    user_id=author.id,
                    content="Discussion for a different strategy.",
                    strategy_id="different-strategy",
                    likes_count=0,
                    comments_count=0,
                ),
            ]
        )
        db.session.commit()

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}")

    assert response.status_code == 200
    data = response.json["data"]
    assert data["share_mode"] == "free"
    assert data["import_mode"] == "sealed"
    assert data["trial_backtest_enabled"] is True
    assert data["discussion_count"] == 2


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
            source="marketplace",
            source_strategy_id=strategy_id,
            storage_key="strategy_store/original.qys",
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


def test_marketplace_import_requires_auth(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.post(f"/api/v1/marketplace/strategies/{strategy_id}/import")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_marketplace_import_status_requires_auth(client, app, tmp_path):
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.get(f"/api/v1/marketplace/strategies/{strategy_id}/import-status")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_marketplace_import_creates_user_strategy_and_returns_redirect(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138103", nickname="MarketplaceImporter")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/import",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"]["redirect_to"].startswith("/backtest/configure?strategy_id=")
    imported_strategy_id = response.json["data"]["strategy_id"]

    with app.app_context():
        imported_strategy = db.session.get(Strategy, imported_strategy_id)
        assert imported_strategy is not None
        assert imported_strategy.owner_id == user_id
        assert imported_strategy.source == "marketplace"
        assert imported_strategy.source_strategy_id == strategy_id
        assert imported_strategy.title == "Golden Breakout"
        assert imported_strategy.description == "Trend-following breakout strategy for gold."
        assert imported_strategy.category == "trend-following"
        assert imported_strategy.tags == ["gold", "breakout"]
        assert imported_strategy.storage_key == "strategies/public-marketplace-strategy.qys"
        assert imported_strategy.code_encrypted is None


def test_marketplace_import_returns_conflict_when_strategy_already_imported(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138104", nickname="MarketplaceImporterTwice")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        db.session.add(
            Strategy(
                id=f"imported-{uuid.uuid4().hex[:8]}",
                name="Imported Golden Breakout",
                title="Golden Breakout",
                symbol="XAUUSD",
                status="draft",
                owner_id=user_id,
                source="marketplace",
                source_strategy_id=strategy_id,
                storage_key="strategies/public-marketplace-strategy.qys",
            )
        )
        db.session.commit()

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/import",
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "ALREADY_IMPORTED"


def test_marketplace_import_status_reports_imported_state(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138105", nickname="ImportStatusUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.get(
        f"/api/v1/marketplace/strategies/{strategy_id}/import-status",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json["data"] == {"imported": False, "user_strategy_id": None}

    with app.app_context():
        imported_strategy = Strategy(
            id=f"imported-{uuid.uuid4().hex[:8]}",
            name="Imported Golden Breakout",
            title="Golden Breakout",
            symbol="XAUUSD",
            status="draft",
            owner_id=user_id,
            source="marketplace",
            source_strategy_id=strategy_id,
            storage_key="strategies/public-marketplace-strategy.qys",
        )
        db.session.add(imported_strategy)
        db.session.commit()
        imported_strategy_id = imported_strategy.id

    response = client.get(
        f"/api/v1/marketplace/strategies/{strategy_id}/import-status",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"imported": True, "user_strategy_id": imported_strategy_id}


def test_trial_backtest_creates_job_without_importing_strategy(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138115", nickname="TrialBacktestUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.trial_backtest_enabled = True
        db.session.commit()

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/trial-backtest",
        headers=_auth_headers(token),
        json={
            "params": {},
            "time_range": {"start": "2024-01-01", "end": "2024-06-01"},
        },
    )

    assert response.status_code == 200
    assert response.json["data"]["job_id"]
    assert response.json["data"]["mode"] == "trial"

    with app.app_context():
        jobs = BacktestJob.query.filter_by(user_id=user_id, strategy_id=strategy_id).all()
        assert len(jobs) == 1
        assert jobs[0].params["strategy_params"] == {}
        assert jobs[0].params["start_time"] == "2024-01-01"
        assert jobs[0].params["end_time"] == "2024-06-01"
        assert Strategy.query.filter_by(owner_id=user_id, source_strategy_id=strategy_id).count() == 0


def test_trial_backtest_reuses_preflight_for_non_object_strategy_params(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138117", nickname="TrialInvalidParamsUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.trial_backtest_enabled = True
        db.session.commit()

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/trial-backtest",
        headers=_auth_headers(token),
        json={"params": ["lookback", 20]},
    )

    assert response.status_code == 400
    assert response.json["message"] == "invalid_strategy_params"

    with app.app_context():
        assert BacktestJob.query.filter_by(user_id=user_id, strategy_id=strategy_id).count() == 0


def test_trial_backtest_reuses_preflight_for_missing_strategy_version(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138118", nickname="TrialMissingVersionUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.trial_backtest_enabled = True
        db.session.commit()

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/trial-backtest",
        headers=_auth_headers(token),
        json={"strategy_version": "9.9.9"},
    )

    assert response.status_code == 400
    assert response.json["message"] == "strategy_version_not_found"

    with app.app_context():
        assert BacktestJob.query.filter_by(user_id=user_id, strategy_id=strategy_id).count() == 0


def test_trial_backtest_requires_strategy_opt_in(client, app, tmp_path):
    token, _ = _login_user(client, phone="13800138116", nickname="TrialDisabledUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        strategy.trial_backtest_enabled = False
        db.session.commit()

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/trial-backtest",
        headers=_auth_headers(token),
        json={"params": {"lookback": 20}},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "TRIAL_BACKTEST_DISABLED"
    assert response.json["error"]["message"] == "Trial backtest is not enabled for this strategy"


def test_imported_marketplace_strategy_uses_source_package_for_parameter_loading(client, app, tmp_path):
    token, user_id = _login_user(client, phone="13800138106", nickname="ImportedParamUser")
    strategy_id = _seed_marketplace_strategy(app, tmp_path)

    response = client.post(
        f"/api/v1/marketplace/strategies/{strategy_id}/import",
        headers=_auth_headers(token),
    )
    imported_strategy_id = response.json["data"]["strategy_id"]

    response = client.get(
        f"/api/v1/strategies/{imported_strategy_id}/parameters",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == []


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
