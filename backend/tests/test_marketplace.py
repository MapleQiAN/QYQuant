from app.extensions import db
from app.models import File, Strategy, StrategyVersion, User


def _create_user(user_id, nickname, avatar_url):
    return User(
        id=user_id,
        phone=None,
        nickname=nickname,
        avatar_url=avatar_url,
    )


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
    meta = response.json["meta"]
    assert meta == {"total": 3, "page": 2, "page_size": 1}


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
        assert any(str(tag).strip().lower() == "onboarding" for tag in (seeded.tags or []))
        assert db.session.get(File, "onboarding-gold-step-file") is not None
        assert StrategyVersion.query.filter_by(strategy_id="onboarding-gold-step", version="0.1.0").count() == 1
