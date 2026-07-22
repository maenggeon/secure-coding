from flask import Blueprint, request

from app.extensions import db
from app.models.transaction import Transaction
from app.models.user import User
from app.services.audit_service import log_event
from app.utils.decorators import active_user_required, csrf_required, login_required
from app.utils.security import error_response, get_client_ip, success_response

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def transfer(user):
    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    amount = data.get("amount")
    idempotency_key = (data.get("idempotency_key") or "").strip()

    if not idempotency_key or len(idempotency_key) > 64:
        return error_response("멱등성 키(idempotency_key)가 필요합니다.", 400)

    existing = Transaction.query.filter_by(idempotency_key=idempotency_key).first()
    if existing:
        return success_response(existing.to_dict(), "이미 처리된 송금입니다.")

    try:
        receiver_id = int(receiver_id)
        amount = int(amount)
    except (TypeError, ValueError):
        return error_response("수신자 ID와 금액이 올바르지 않습니다.", 400)

    if receiver_id == user.id:
        return error_response("자기 자신에게 송금할 수 없습니다.", 400)

    if amount <= 0 or amount > 10_000_000:
        return error_response("송금액은 1~10,000,000원 사이여야 합니다.", 400)

    receiver = User.query.get(receiver_id)
    if not receiver or receiver.status == "DELETED":
        return error_response("수신자를 찾을 수 없습니다.", 404)

    if receiver.is_blocked():
        return error_response("수신자 계정이 제재 상태입니다.", 400)

    sender = User.query.filter_by(id=user.id).with_for_update().first()
    receiver_locked = User.query.filter_by(id=receiver_id).with_for_update().first()

    if sender.balance < amount:
        db.session.rollback()
        return error_response("잔액이 부족합니다.", 400)

    sender.balance -= amount
    receiver_locked.balance += amount

    transaction = Transaction(
        sender_id=sender.id,
        receiver_id=receiver_locked.id,
        amount=amount,
        idempotency_key=idempotency_key,
    )
    db.session.add(transaction)
    db.session.commit()

    log_event(
        sender.id,
        "TRANSFER",
        f"to={receiver_id}, amount={amount}, tx_id={transaction.id}",
        get_client_ip(),
    )

    return success_response(transaction.to_dict(), "송금이 완료되었습니다.", 201)
