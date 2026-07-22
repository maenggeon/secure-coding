from datetime import datetime, timezone

from flask import Blueprint, request

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.services.audit_service import log_event
from app.utils.decorators import admin_required, csrf_required
from app.utils.security import error_response, get_client_ip, sanitize_text, success_response

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users(admin):
    users = User.query.filter(User.status != "DELETED").order_by(User.created_at.desc()).all()
    return success_response([u.to_private_dict() for u in users])


@admin_bp.route("/products", methods=["GET"])
@admin_required
def list_all_products(admin):
    products = Product.query.filter(Product.status != "DELETED").order_by(Product.created_at.desc()).all()
    return success_response([p.to_detail_dict() for p in products])


@admin_bp.route("/reports", methods=["GET"])
@admin_required
def list_reports(admin):
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return success_response([r.to_dict() for r in reports])


@admin_bp.route("/reports/<int:report_id>", methods=["PATCH"])
@admin_required
@csrf_required
def process_report(admin, report_id):
    report = Report.query.get(report_id)
    if not report:
        return error_response("신고 내역을 찾을 수 없습니다.", 404)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").upper()
    admin_note = sanitize_text(data.get("admin_note"), 500)

    if action not in ("APPROVE", "REJECT"):
        return error_response("action은 APPROVE 또는 REJECT여야 합니다.", 400)

    report.status = "APPROVED" if action == "APPROVE" else "REJECTED"
    report.admin_note = admin_note
    report.processed_at = datetime.now(timezone.utc)

    if action == "APPROVE":
        if report.target_type == "PRODUCT":
            product = Product.query.get(report.target_id)
            if product:
                product.status = "BLOCKED"
        elif report.target_type == "USER":
            target_user = User.query.get(report.target_id)
            if target_user:
                target_user.status = "BLOCKED"

    db.session.commit()
    log_event(admin.id, "REPORT_PROCESS", f"report_id={report_id}, action={action}", get_client_ip())
    return success_response(report.to_dict(), "신고가 처리되었습니다.")


@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@admin_required
@csrf_required
def update_user_status(admin, user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("사용자를 찾을 수 없습니다.", 404)

    if user.is_admin():
        return error_response("관리자 계정 상태는 변경할 수 없습니다.", 403)

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").upper()

    if status not in ("ACTIVE", "SUSPENDED", "BLOCKED", "DELETED"):
        return error_response("올바른 상태값이 아닙니다.", 400)

    user.status = status
    db.session.commit()
    log_event(admin.id, "USER_STATUS_CHANGE", f"user_id={user_id}, status={status}", get_client_ip())
    return success_response(user.to_private_dict(), "사용자 상태가 변경되었습니다.")


@admin_bp.route("/products/<int:product_id>/status", methods=["PATCH"])
@admin_required
@csrf_required
def update_product_status(admin, product_id):
    product = Product.query.get(product_id)
    if not product:
        return error_response("상품을 찾을 수 없습니다.", 404)

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").upper()

    if status not in ("ACTIVE", "BLOCKED"):
        return error_response("올바른 상태값이 아닙니다.", 400)

    product.status = status
    db.session.commit()
    log_event(admin.id, "PRODUCT_STATUS_CHANGE", f"product_id={product_id}, status={status}", get_client_ip())
    return success_response(product.to_detail_dict(), "상품 상태가 변경되었습니다.")


@admin_bp.route("/logs", methods=["GET"])
@admin_required
def get_audit_logs(admin):
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return success_response([log.to_dict() for log in logs])
