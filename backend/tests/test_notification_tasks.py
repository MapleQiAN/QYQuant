from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models import User


def test_render_strategy_review_email_formats_subject_and_bodies():
    from app.utils.email_templates import render_strategy_review_email

    subject, body_html, body_text = render_strategy_review_email(
        strategy_name="Golden Breakout",
        status="approved",
    )

    assert subject == "[QYQuant] 您的策略审核结果通知"
    assert "Golden Breakout" in body_html
    assert "审核结果：通过" in body_html
    assert "Golden Breakout" in body_text
    assert "审核结果：通过" in body_text


def test_send_email_notification_sends_strategy_review_result_email(monkeypatch, app):
    from app.tasks.notification_tasks import send_email_notification

    sent_messages = []

    with app.app_context():
        user = User(phone="13800138907", nickname="MailOwner", email="owner@example.com")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.notification_tasks.mail",
        SimpleNamespace(send=lambda message: sent_messages.append(message)),
    )

    result = send_email_notification.run(
        user_id=user_id,
        event_type="strategy_review_result",
        context_data={
            "strategy_name": "Golden Breakout",
            "status": "approved",
            "target_id": "strategy-1",
        },
    )

    assert result == {"ok": True, "skipped": False}
    assert len(sent_messages) == 1
    assert sent_messages[0].recipients == ["owner@example.com"]
    assert sent_messages[0].subject == "[QYQuant] 您的策略审核结果通知"
    assert "Golden Breakout" in sent_messages[0].body
    assert "Golden Breakout" in sent_messages[0].html


def test_send_email_notification_is_idempotent_for_same_target(monkeypatch, app):
    from app.tasks.notification_tasks import reset_email_idempotency_state, send_email_notification

    sent_messages = []
    reset_email_idempotency_state()

    with app.app_context():
        user = User(phone="13800138908", nickname="MailOwner2", email="owner2@example.com")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.notification_tasks.mail",
        SimpleNamespace(send=lambda message: sent_messages.append(message)),
    )

    payload = {
        "strategy_name": "Momentum Alpha",
        "status": "approved",
        "target_id": "strategy-2",
    }
    first = send_email_notification.run(user_id=user_id, event_type="strategy_review_result", context_data=payload)
    second = send_email_notification.run(user_id=user_id, event_type="strategy_review_result", context_data=payload)

    assert first == {"ok": True, "skipped": False}
    assert second == {"ok": True, "skipped": True}
    assert len(sent_messages) == 1


def test_send_email_notification_retries_when_mail_send_fails(monkeypatch, app):
    from app.tasks.notification_tasks import send_email_notification

    class RetryTriggered(Exception):
        pass

    with app.app_context():
        user = User(phone="13800138909", nickname="RetryOwner", email="retry@example.com")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    monkeypatch.setattr(
        "app.tasks.notification_tasks.mail",
        SimpleNamespace(send=lambda message: (_ for _ in ()).throw(RuntimeError("smtp unavailable"))),
    )
    monkeypatch.setattr(send_email_notification, "request", SimpleNamespace(retries=1))

    def _retry(*, exc, countdown):
        raise RetryTriggered((str(exc), countdown))

    monkeypatch.setattr(send_email_notification, "retry", _retry)

    with pytest.raises(RetryTriggered) as exc_info:
        send_email_notification.run(
            user_id=user_id,
            event_type="strategy_review_result",
            context_data={
                "strategy_name": "Retry Strategy",
                "status": "rejected",
                "reason": "风险披露不完整",
                "target_id": "strategy-3",
            },
        )

    assert exc_info.value.args[0] == ("smtp unavailable", 120)
