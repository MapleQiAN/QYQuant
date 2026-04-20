import json


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138900", nickname="ReportUser"):
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


def test_backtest_report_row_belongs_to_completed_job(app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User

    with app.app_context():
        user = User(phone="13800138901", nickname="ReportOwner")
        db.session.add(user)
        db.session.flush()

        job = BacktestJob(
            user_id=user.id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()

        report = BacktestReport(backtest_job_id=job.id, user_id=user.id, status="pending")
        db.session.add(report)
        db.session.commit()

        stored = BacktestReport.query.filter_by(backtest_job_id=job.id).one()
        assert stored.user_id == user.id
        assert stored.status == "pending"


def _build_report_fixture():
    base_time = 1700000000000
    bars = [
        {
            "time": base_time,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1000,
        },
        {
            "time": base_time + 86_400_000,
            "open": 100.0,
            "high": 108.0,
            "low": 99.0,
            "close": 105.0,
            "volume": 1100,
        },
        {
            "time": base_time + 2 * 86_400_000,
            "open": 105.0,
            "high": 111.0,
            "low": 104.0,
            "close": 110.0,
            "volume": 1200,
        },
        {
            "time": base_time + 3 * 86_400_000,
            "open": 110.0,
            "high": 112.0,
            "low": 107.0,
            "close": 108.0,
            "volume": 1250,
        },
        {
            "time": base_time + 4 * 86_400_000,
            "open": 108.0,
            "high": 109.0,
            "low": 101.0,
            "close": 102.0,
            "volume": 1300,
        },
    ]
    trades = [
        {
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 100.0,
            "quantity": 10.0,
            "timestamp": base_time,
            "pnl": None,
        },
        {
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 110.0,
            "quantity": 10.0,
            "timestamp": base_time + 2 * 86_400_000,
            "pnl": 100.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 108.0,
            "quantity": 5.0,
            "timestamp": base_time + 3 * 86_400_000,
            "pnl": None,
        },
        {
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 102.0,
            "quantity": 5.0,
            "timestamp": base_time + 4 * 86_400_000,
            "pnl": -30.0,
        },
    ]
    return bars, trades


def test_compute_all_metrics_returns_report_structures():
    from app.report_agent.quant_engine import compute_all_metrics

    bars, trades = _build_report_fixture()

    report = compute_all_metrics(bars, trades)

    assert {
        "totalReturn",
        "annualizedReturn",
        "maxDrawdown",
        "sharpeRatio",
        "volatility",
        "sortinoRatio",
        "calmarRatio",
        "winRate",
        "profitLossRatio",
        "maxConsecutiveLosses",
        "avgHoldingDays",
        "totalTrades",
        "alpha",
        "beta",
    }.issubset(set(report["metrics"].keys()))
    assert len(report["equity_curve"]) == len(bars)
    assert len(report["drawdown_series"]) == len(bars)
    assert report["monthly_returns"]
    assert len(report["trade_details"]) == len(trades)


def test_build_report_payload_preserves_normalized_series():
    from app.report_agent.quant_engine import build_report_payload

    bars, trades = _build_report_fixture()

    payload = build_report_payload(bars, trades)

    assert payload["equity_curve"][0]["timestamp"] == bars[0]["time"]
    assert payload["drawdown_series"][-1]["timestamp"] == bars[-1]["time"]
    assert payload["monthly_returns"][0]["month"]
    assert payload["trade_details"][0]["side"] == "buy"
    assert payload["trade_details"][-1]["pnl"] == -30.0


def test_filter_report_for_free_tier_hides_ai_and_diagnostics():
    from app.report_agent.tier_filter import filter_report_for_tier

    report = {
        "metrics": {
            "totalReturn": 10,
            "annualizedReturn": 12,
            "maxDrawdown": -3,
            "sharpeRatio": 1.2,
            "volatility": 8.1,
            "winRate": 55.0,
            "totalTrades": 22,
            "omegaRatio": 1.7,
        },
        "executive_summary": "summary",
        "metric_narrations": {"sharpeRatio": "good"},
        "anomalies": [{"title": "outlier"}],
        "advisor_narration": "upgrade",
    }

    filtered = filter_report_for_tier(report, "free")
    assert filtered["metrics"] == {
        "totalReturn": 10,
        "annualizedReturn": 12,
        "maxDrawdown": -3,
        "sharpeRatio": 1.2,
        "volatility": 8.1,
        "winRate": 55.0,
        "totalTrades": 22,
    }
    assert "advisor_narration" not in filtered
    assert "anomalies" not in filtered
    assert "metric_narrations" not in filtered
    assert "executive_summary" in filtered


def test_generate_report_upserts_existing_report_row(app, monkeypatch, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User
    from app.utils.storage import build_backtest_storage_key, write_json

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", tmp_path.as_posix())

    with app.app_context():
        user = User(phone="13800138902", nickname="AsyncOwner")
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_storage_key=build_backtest_storage_key("async-job"),
        )
        job.id = "async-job"
        db.session.add(job)
        db.session.commit()

    bars, trades = _build_report_fixture()
    storage_key = build_backtest_storage_key("async-job")
    write_json(f"{storage_key}/kline.json", bars)
    write_json(f"{storage_key}/trades.json", trades)

    from app.report_agent.orchestrator import generate_report

    with app.app_context():
        first = generate_report("async-job", user_id)
        second = generate_report("async-job", user_id, force=True)

        stored = BacktestReport.query.filter_by(backtest_job_id="async-job").all()
        assert len(stored) == 1
        assert first.id == second.id
        assert stored[0].status == "ready"
        assert stored[0].metrics["totalReturn"] is not None
        assert stored[0].equity_curve


def test_post_backtest_report_creates_regeneration_request(client, app, monkeypatch):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus

    token, user_id = _login_user(client, phone="13800138903", nickname="ReportPoster")
    queued = {}

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    def _fake_delay(job_id, user_id, force=False, locale="en"):
        queued["job_id"] = job_id
        queued["user_id"] = user_id
        queued["force"] = force
        queued["locale"] = locale

    monkeypatch.setattr("app.tasks.report_generation.generate_backtest_report.delay", _fake_delay)

    response = client.post(f"/api/backtests/{job_id}/report", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"]["job_id"] == job_id
    assert response.json["data"]["status"] == "pending"
    assert response.json["data"]["report_id"] is not None
    assert queued == {
        "job_id": job_id,
        "user_id": user_id,
        "force": True,
        "locale": "en",
    }


def test_get_report_returns_tier_filtered_payload(client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User

    token, user_id = _login_user(client, phone="13800138904", nickname="TierReader")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "free"
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
            metrics={
                "totalReturn": 12.5,
                "annualizedReturn": 10.2,
                "maxDrawdown": -3.0,
                "sharpeRatio": 1.6,
                "volatility": 8.5,
                "winRate": 55,
                "totalTrades": 24,
                "alpha": 1.1,
            },
            equity_curve=[{"timestamp": 1, "equity": 101000.0, "benchmark_equity": 100500.0}],
            drawdown_series=[{"timestamp": 1, "drawdown": -1.2}],
            monthly_returns=[{"month": "2024-01", "return": 3.2}],
            trade_details=[{"symbol": "BTCUSDT", "side": "buy", "price": 100.0, "quantity": 1.0, "timestamp": 1}],
            executive_summary="summary",
            metric_narrations={"sharpeRatio": "good"},
            anomalies=[{"title": "outlier"}],
            advisor_narration="upgrade",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    response = client.get(f"/api/reports/{report_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == report_id
    assert data["status"] == "ready"
    assert data["payload"]["metrics"]["totalReturn"] == 12.5
    assert "alpha" not in data["payload"]["metrics"]
    assert "anomalies" not in data["payload"]
    assert "advisor_narration" not in data["payload"]
    assert data["payload"]["executive_summary"] == "summary"


def test_get_report_status_returns_report_state(client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport

    token, user_id = _login_user(client, phone="13800138905", nickname="StatusReader")

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        job_id = job.id
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="computing",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    response = client.get(f"/api/reports/{report_id}/status", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"] == {
        "id": report_id,
        "job_id": job_id,
        "status": "computing",
    }


def test_report_status_stream_emits_sse_frame(client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport

    token, user_id = _login_user(client, phone="13800138906", nickname="StreamReader")

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    response = client.get(f"/api/reports/{report_id}/status/stream?token={token}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "data:" in body
    assert '"status": "ready"' in body


def test_legacy_report_route_exposes_async_report_compat_fields(client, app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", tmp_path.as_posix())
    token, user_id = _login_user(client, phone="13800138907", nickname="CompatReader")

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_summary={"totalReturn": 5.5},
            result_storage_key="backtest-results/compat-job",
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
        )
        db.session.add(report)
        db.session.commit()
        job_id = job.id
        report_id = report.id

    root = tmp_path / "backtest-results" / "compat-job"
    root.mkdir(parents=True)
    (root / "equity_curve.json").write_text(
        json.dumps([{"timestamp": 1, "equity": 100000.0, "benchmark_equity": 100000.0}], ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "trades.json").write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")
    (root / "kline.json").write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    response = client.get(f"/api/v1/backtest/{job_id}/report", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"]["report_id"] == report_id
    assert response.json["data"]["report_status"] == "ready"


def test_generate_report_uses_narrator_stub(app, monkeypatch, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User
    from app.utils.storage import build_backtest_storage_key, write_json

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", tmp_path.as_posix())
    monkeypatch.setattr("app.report_agent.narrator.generate_summary", lambda metrics, tier, locale="en": f"{tier} summary")
    monkeypatch.setattr("app.report_agent.narrator.annotate_metrics", lambda metrics, locale="en": {"sharpeRatio": "stub metric"})

    with app.app_context():
        user = User(phone="13800138908", nickname="NarratorOwner", plan_level="go")
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_storage_key=build_backtest_storage_key("narrator-job"),
        )
        job.id = "narrator-job"
        db.session.add(job)
        db.session.commit()

    bars, trades = _build_report_fixture()
    storage_key = build_backtest_storage_key("narrator-job")
    write_json(f"{storage_key}/kline.json", bars)
    write_json(f"{storage_key}/trades.json", trades)

    from app.report_agent.orchestrator import generate_report

    with app.app_context():
        report = generate_report("narrator-job", user_id, force=True)
        stored = db.session.get(BacktestReport, report.id)

        assert stored.executive_summary == "go summary"
        assert stored.metric_narrations == {"sharpeRatio": "stub metric"}


def test_generate_report_uses_diagnostician_for_plus_tier(app, monkeypatch, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User
    from app.utils.storage import build_backtest_storage_key, write_json

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", tmp_path.as_posix())
    monkeypatch.setattr("app.report_agent.diagnostician.generate_diagnosis", lambda payload, tier, locale="en": "diagnosis stub")

    with app.app_context():
        user = User(phone="13800138909", nickname="DiagnosisOwner", plan_level="plus")
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_storage_key=build_backtest_storage_key("diagnosis-job"),
        )
        job.id = "diagnosis-job"
        db.session.add(job)
        db.session.commit()

    bars, trades = _build_report_fixture()
    storage_key = build_backtest_storage_key("diagnosis-job")
    write_json(f"{storage_key}/kline.json", bars)
    write_json(f"{storage_key}/trades.json", trades)

    from app.report_agent.orchestrator import generate_report

    with app.app_context():
        report = generate_report("diagnosis-job", user_id, force=True)
        stored = db.session.get(BacktestReport, report.id)

        assert stored.diagnosis_narration == "diagnosis stub"


def test_generate_report_uses_advisor_and_creates_alerts_for_pro_tier(app, monkeypatch, tmp_path):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, ReportAlert, User
    from app.utils.storage import build_backtest_storage_key, write_json

    monkeypatch.setenv("BACKTEST_STORAGE_DIR", tmp_path.as_posix())
    monkeypatch.setattr("app.report_agent.advisor.generate_suggestions", lambda payload, tier, locale="en": "advisor stub")
    monkeypatch.setattr(
        "app.report_agent.advisor.generate_alerts",
        lambda payload, tier, locale="en": [{"level": "warning", "title": "Drawdown cluster", "message": "Watch recent losses"}],
    )

    with app.app_context():
        user = User(phone="13800138910", nickname="AdvisorOwner", plan_level="pro")
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
            result_storage_key=build_backtest_storage_key("advisor-job"),
        )
        job.id = "advisor-job"
        db.session.add(job)
        db.session.commit()

    bars, trades = _build_report_fixture()
    storage_key = build_backtest_storage_key("advisor-job")
    write_json(f"{storage_key}/kline.json", bars)
    write_json(f"{storage_key}/trades.json", trades)

    from app.report_agent.orchestrator import generate_report

    with app.app_context():
        report = generate_report("advisor-job", user_id, force=True)
        stored = db.session.get(BacktestReport, report.id)
        alert = ReportAlert.query.filter_by(report_id=report.id).one()

        assert stored.advisor_narration == "advisor stub"
        assert alert.level == "warning"
        assert alert.title == "Drawdown cluster"


def test_report_chat_persists_question_and_answer(client, app, monkeypatch):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, ReportChatMessage, User

    token, user_id = _login_user(client, phone="13800138911", nickname="ChatOwner")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "plus"
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
            metrics={"totalReturn": 12.5},
            executive_summary="summary",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    monkeypatch.setattr("app.report_agent.chat_router.route_chat_question", lambda message, report, locale="en": "answer stub")

    response = client.post(
        f"/api/reports/{report_id}/chat",
        headers=_auth_headers(token),
        json={"message": "What is the main risk?"},
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "answer stub"

    with app.app_context():
        rows = ReportChatMessage.query.filter_by(report_id=report_id).order_by(ReportChatMessage.created_at.asc()).all()
        assert [row.role for row in rows] == ["user", "assistant"]
        assert rows[0].message == "What is the main risk?"
        assert rows[1].message == "answer stub"

    history = client.get(f"/api/reports/{report_id}/chat/history", headers=_auth_headers(token))

    assert history.status_code == 200
    assert [item["role"] for item in history.json["data"]["messages"]] == ["user", "assistant"]


def test_report_chat_rejects_free_tier(client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport

    token, user_id = _login_user(client, phone="13800138912", nickname="FreeChatOwner")

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    response = client.post(
        f"/api/reports/{report_id}/chat",
        headers=_auth_headers(token),
        json={"message": "Can I chat?"},
    )

    assert response.status_code == 403


def test_report_alerts_can_be_listed_and_dismissed(client, app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, ReportAlert

    token, user_id = _login_user(client, phone="13800138913", nickname="AlertOwner")

    with app.app_context():
        job = BacktestJob(
            user_id=user_id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(
            backtest_job_id=job.id,
            user_id=user_id,
            status="ready",
        )
        db.session.add(report)
        db.session.flush()
        alert = ReportAlert(
            report_id=report.id,
            user_id=user_id,
            level="warning",
            title="Risk spike",
            message="Drawdown increased",
        )
        db.session.add(alert)
        db.session.commit()
        report_id = report.id
        alert_id = alert.id

    list_response = client.get(f"/api/reports/{report_id}/alerts", headers=_auth_headers(token))

    assert list_response.status_code == 200
    assert list_response.json["data"]["alerts"][0]["title"] == "Risk spike"

    dismiss_response = client.post(
        f"/api/reports/{report_id}/alerts/{alert_id}/dismiss",
        headers=_auth_headers(token),
    )

    assert dismiss_response.status_code == 200

    with app.app_context():
        stored = db.session.get(ReportAlert, alert_id)
        assert stored.status == "dismissed"
