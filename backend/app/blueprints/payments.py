from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import PaymentOrder, User
from ..utils.response import error_response, ok


bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')

PLAN_PRICES = {
    "free": 0,
    "lite": 200,
    "pro": 500,
    "expert": 1000,
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
