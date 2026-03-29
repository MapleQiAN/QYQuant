from datetime import timedelta

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import AuditLog, PaymentOrder, Subscription, User
from ..quota import ensure_user_quota, serialize_plan_limit
from ..services.notifications import create_notification
from ..utils.response import error_response, ok
from ..utils.time import next_month_start_beijing, now_utc


bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')

PLAN_PRICES = {
    "free": 0,
    "go": 50,
    "plus": 200,
    "pro": 500,
    "ultra": 1000,
}
PAYABLE_PLAN_LEVELS = tuple(plan_level for plan_level in PLAN_PRICES if plan_level != "free")
VALID_PROVIDERS = ("wechat", "alipay")


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response("USER_NOT_FOUND", "user not found", 404)
    return user, None


def _serialize_order(order):
    return {
        "order_id": order.id,
        "pay_url": order.pay_url,
        "plan_level": order.plan_level,
        "amount": float(order.amount),
        "provider": order.provider,
    }


def _generate_pay_url(provider, plan_level, amount):
    if current_app.config.get("PAYMENT_SANDBOX", True):
        return f"https://pay.mock.example.com/{provider}/{plan_level}?amount={amount}"
    raise NotImplementedError("Production payment integration is not available in story 8.2")


@bp.post('/orders')
@jwt_required()
def create_payment_order():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    plan_level = (payload.get("plan_level") or "").strip()
    provider = (payload.get("provider") or "").strip()

    if plan_level not in PAYABLE_PLAN_LEVELS:
        valid_values = ", ".join(PAYABLE_PLAN_LEVELS)
        return error_response("INVALID_PLAN", f"valid plan_level values: {valid_values}", 400)

    if provider not in VALID_PROVIDERS:
        valid_values = ", ".join(VALID_PROVIDERS)
        return error_response("INVALID_PROVIDER", f"valid provider values: {valid_values}", 400)

    existing_order = (
        PaymentOrder.query
        .filter_by(user_id=user.id, plan_level=plan_level, status='pending')
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    if existing_order is not None:
        return ok(_serialize_order(existing_order))

    amount = PLAN_PRICES[plan_level]
    order = PaymentOrder(
        user_id=user.id,
        plan_level=plan_level,
        amount=amount,
        provider=provider,
        pay_url=_generate_pay_url(provider, plan_level, amount),
        status='pending',
    )
    db.session.add(order)
    db.session.commit()

    return ok(_serialize_order(order)), 201


def _activate_subscription(order, provider_order_id=None):
    """
    原子性地激活订阅。
    - 更新 PaymentOrder.status = 'paid'
    - 创建 Subscription 记录（1个月有效期）
    - 更新 User.plan_level 和 UserQuota.plan_level
    - 写入 AuditLog
    - 发送站内通知
    注意：调用者需在函数外部负责 db.session.commit()
    """
    starts_at = now_utc()
    ends_at = starts_at + timedelta(days=31)

    order.status = 'paid'
    if provider_order_id:
        order.provider_order_id = provider_order_id

    subscription = Subscription(
        user_id=order.user_id,
        plan_level=order.plan_level,
        starts_at=starts_at,
        ends_at=ends_at,
        status='active',
        payment_provider=order.provider,
        payment_order_id=order.id,
    )
    db.session.add(subscription)

    user = db.session.get(User, order.user_id)
    if user:
        user.plan_level = order.plan_level

    quota = ensure_user_quota(order.user_id, order.plan_level)
    quota.reset_at = next_month_start_beijing(starts_at)

    audit = AuditLog(
        operator_id=None,
        action='subscription_activated',
        target_type='user',
        target_id=order.user_id,
        details={
            'order_id': order.id,
            'plan_level': order.plan_level,
            'provider': order.provider,
            'amount': float(order.amount),
        },
    )
    db.session.add(audit)

    quota_display = serialize_plan_limit(order.plan_level)
    if quota_display == 'unlimited':
        quota_text = '无限次'
    else:
        quota_text = f'{quota_display} 次'
    create_notification(
        user_id=order.user_id,
        type='subscription_activated',
        title='套餐升级成功',
        content=f'您已成功升级为 {order.plan_level} 套餐，已解锁 {quota_text}/月回测额度。',
    )


@bp.post('/webhook/wechat')
def wechat_webhook():
    if current_app.config.get("PAYMENT_SANDBOX", True):
        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id') or payload.get('out_trade_no')
        provider_order_id = payload.get('transaction_id')
    else:
        return error_response('SIGNATURE_INVALID', '签名验证失败', 400)

    if not order_id:
        return error_response('INVALID_CALLBACK', '无效回调参数', 400)

    order = db.session.get(PaymentOrder, order_id)
    if order is None:
        return error_response('INVALID_CALLBACK', '无效回调参数', 400)

    if order.status == 'paid':
        return ok({'message': 'ok'})

    if order.status != 'pending':
        return error_response('INVALID_CALLBACK', '无效回调参数', 400)

    _activate_subscription(order, provider_order_id=provider_order_id)
    db.session.commit()

    return ok({'message': 'ok'})


@bp.post('/webhook/alipay')
def alipay_webhook():
    if current_app.config.get("PAYMENT_SANDBOX", True):
        order_id = (
            request.form.get('out_trade_no')
            or (request.get_json(silent=True) or {}).get('order_id')
        )
        provider_order_id = (
            request.form.get('trade_no')
            or (request.get_json(silent=True) or {}).get('trade_no')
        )
    else:
        return 'fail', 400

    if not order_id:
        return 'fail', 400

    order = db.session.get(PaymentOrder, order_id)
    if order is None:
        return 'fail', 400

    if order.status == 'paid':
        return 'success', 200

    if order.status != 'pending':
        return 'fail', 400

    _activate_subscription(order, provider_order_id=provider_order_id)
    db.session.commit()

    return 'success', 200
