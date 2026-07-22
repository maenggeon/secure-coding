from datetime import datetime, timezone

from flask import Blueprint, current_app, request

from app.extensions import db
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.services.audit_service import log_event
from app.utils.decorators import active_user_required, csrf_required, login_required
from app.utils.security import error_response, get_client_ip, sanitize_text, success_response

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def create_report(user):
    data = request.get_json(silent=True) or {}
    target_type = (data.get("target_type") or "").upper()
    target_id = data.get("target_id")
    reason = sanitize_text(data.get("reason"), 1000)

    if target_type not in ("USER", "PRODUCT"):
        return error_response("신고 대상 유형이 올바르지 않습니다.", 400)

    try:
        target_id = int(target_id)
    except (TypeError, ValueError):
        return error_response("신고 대상 ID가 올바르지 않습니다.", 400)

    if not reason or len(reason) < 10:
        return error_response("신고 사유는 10자 이상 입력해야 합니다.", 400)

    if target_type == "USER":
        target = User.query.get(target_id)
        if not target or target.status == "DELETED":
            return error_response("신고 대상 사용자를 찾을 수 없습니다.", 404)
        if target_id == user.id:
            return error_response("자기 자신을 신고할 수 없습니다.", 400)
    else:
        target = Product.query.get(target_id)
        if not target or target.status == "DELETED":
            return error_response("신고 대상 상품을 찾을 수 없습니다.", 404)

    existing = Report.query.filter_by(
        reporter_id=user.id, target_type=target_type, target_id=target_id
    ).first()
    if existing:
        return error_response("이미 신고한 대상입니다.", 409)

    report = Report(
        reporter_id=user.id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
    )
    db.session.add(report)

    if target_type == "PRODUCT":
        target.report_count += 1
        threshold = current_app.config["AUTO_BLOCK_REPORT_THRESHOLD"]
        if target.report_count >= threshold:
            target.status = "BLOCKED"
            log_event(None, "PRODUCT_AUTO_BLOCKED", f"product_id={target_id}", get_client_ip())

    db.session.commit()
    log_event(user.id, "REPORT_CREATE", f"type={target_type}, id={target_id}", get_client_ip())
    return success_response(report.to_dict(), "신고가 접수되었습니다.", 201)
