from flask import Blueprint, request

from app.extensions import db
from app.models.product import Product
from app.models.user import User
from app.services.audit_service import log_event
from app.utils.decorators import active_user_required, csrf_required, login_required
from app.utils.security import (
    error_response,
    get_client_ip,
    hash_password,
    sanitize_text,
    success_response,
    validate_password,
    verify_password,
)

users_bp = Blueprint("users", __name__)


@users_bp.route("/me", methods=["GET"])
@login_required
def get_me(user):
    return success_response(user.to_private_dict())


@users_bp.route("/me", methods=["PATCH"])
@login_required
@csrf_required
@active_user_required
def update_me(user):
    data = request.get_json(silent=True) or {}
    nickname = data.get("nickname")
    bio = data.get("bio")

    if nickname is not None:
        nickname = sanitize_text(nickname, 50)
        if not nickname:
            return error_response("닉네임을 입력해주세요.", 400)
        user.nickname = nickname

    if bio is not None:
        user.bio = sanitize_text(bio, 500)

    db.session.commit()
    log_event(user.id, "PROFILE_UPDATE", None, get_client_ip())
    return success_response(user.to_private_dict(), "프로필이 수정되었습니다.")


@users_bp.route("/me/password", methods=["PATCH"])
@login_required
@csrf_required
def change_password(user):
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not verify_password(current_password, user.password_hash):
        return error_response("현재 비밀번호가 올바르지 않습니다.", 400)

    valid, msg = validate_password(new_password)
    if not valid:
        return error_response(msg, 400)

    user.password_hash = hash_password(new_password)
    db.session.commit()
    log_event(user.id, "PASSWORD_CHANGE", None, get_client_ip())
    return success_response(message="비밀번호가 변경되었습니다.")


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user or user.status == "DELETED":
        return error_response("사용자를 찾을 수 없습니다.", 404)

    return success_response(user.to_public_dict(include_products=True))


@users_bp.route("/me/products", methods=["GET"])
@login_required
def get_my_products(user):
    products = Product.query.filter_by(seller_id=user.id).order_by(Product.created_at.desc()).all()
    return success_response([p.to_list_dict() for p in products])


@users_bp.route("/me/reports", methods=["GET"])
@login_required
def get_my_reports(user):
    from app.models.report import Report

    reports = Report.query.filter_by(reporter_id=user.id).order_by(Report.created_at.desc()).all()
    return success_response([r.to_dict() for r in reports])


@users_bp.route("/me/transactions", methods=["GET"])
@login_required
def get_my_transactions(user):
    from app.models.transaction import Transaction

    transactions = (
        Transaction.query.filter(
            (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return success_response([t.to_dict() for t in transactions])
