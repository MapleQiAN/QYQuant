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
