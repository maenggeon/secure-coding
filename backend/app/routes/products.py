import os

from flask import Blueprint, current_app, request

from app.extensions import db
from app.models.product import Product
from app.services.audit_service import log_event
from app.utils.decorators import active_user_required, csrf_required, login_required
from app.utils.security import error_response, get_client_ip, sanitize_text, save_product_image, success_response

products_bp = Blueprint("products", __name__)


@products_bp.route("", methods=["GET"])
def list_products():
    query_str = (request.args.get("q") or "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(50, max(1, request.args.get("per_page", 20, type=int)))

    query = Product.query.filter_by(status="ACTIVE")

    if query_str:
        query = query.filter(Product.name.contains(query_str))

    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        {
            "items": [p.to_list_dict() for p in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    )


@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product or product.status in ("DELETED", "BLOCKED"):
        return error_response("상품을 찾을 수 없습니다.", 404)

    return success_response(product.to_detail_dict())


@products_bp.route("", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def create_product(user):
    name = sanitize_text(request.form.get("name"), 200)
    description = sanitize_text(request.form.get("description"), 2000)

    try:
        price = int(request.form.get("price", 0))
    except (TypeError, ValueError):
        return error_response("올바른 가격을 입력해주세요.", 400)

    if not name:
        return error_response("상품명을 입력해주세요.", 400)
    if price < 0 or price > 100_000_000:
        return error_response("가격은 0~100,000,000원 사이여야 합니다.", 400)
    if not description:
        return error_response("상품 설명을 입력해주세요.", 400)

    image_path = None
    if "image" in request.files:
        image_path, err = save_product_image(request.files["image"])
        if err:
            return error_response(err, 400)

    product = Product(
        seller_id=user.id,
        name=name,
        price=price,
        description=description,
        image_path=image_path,
    )
    db.session.add(product)
    db.session.commit()

    log_event(user.id, "PRODUCT_CREATE", f"product_id={product.id}", get_client_ip())
    return success_response(product.to_detail_dict(), "상품이 등록되었습니다.", 201)


@products_bp.route("/<int:product_id>", methods=["PATCH"])
@login_required
@csrf_required
@active_user_required
def update_product(user, product_id):
    product = Product.query.get(product_id)
    if not product or product.status == "DELETED":
        return error_response("상품을 찾을 수 없습니다.", 404)

    if product.seller_id != user.id and not user.is_admin():
        log_event(user.id, "IDOR_ATTEMPT", f"product_id={product_id}", get_client_ip())
        return error_response("수정 권한이 없습니다.", 403)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = sanitize_text(data["name"], 200)
        if not name:
            return error_response("상품명을 입력해주세요.", 400)
        product.name = name

    if "description" in data:
        product.description = sanitize_text(data["description"], 2000)

    if "price" in data:
        try:
            price = int(data["price"])
        except (TypeError, ValueError):
            return error_response("올바른 가격을 입력해주세요.", 400)
        if price < 0 or price > 100_000_000:
            return error_response("가격은 0~100,000,000원 사이여야 합니다.", 400)
        product.price = price

    db.session.commit()
    log_event(user.id, "PRODUCT_UPDATE", f"product_id={product_id}", get_client_ip())
    return success_response(product.to_detail_dict(), "상품이 수정되었습니다.")


@products_bp.route("/<int:product_id>", methods=["DELETE"])
@login_required
@csrf_required
@active_user_required
def delete_product(user, product_id):
    product = Product.query.get(product_id)
    if not product or product.status == "DELETED":
        return error_response("상품을 찾을 수 없습니다.", 404)

    if product.seller_id != user.id and not user.is_admin():
        log_event(user.id, "IDOR_ATTEMPT", f"product_id={product_id}", get_client_ip())
        return error_response("삭제 권한이 없습니다.", 403)

    product.status = "DELETED"
    db.session.commit()
    log_event(user.id, "PRODUCT_DELETE", f"product_id={product_id}", get_client_ip())
    return success_response(message="상품이 삭제되었습니다.")
