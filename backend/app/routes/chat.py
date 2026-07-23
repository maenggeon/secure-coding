from flask import Blueprint, request

from app.extensions import db, socketio
from app.models.chat import ChatMessage, ChatParticipant, ChatRoom
from app.models.product import Product
from app.models.user import User
from app.services.audit_service import log_event
from app.services.chat_service import (
    ensure_global_participant,
    get_or_create_direct_room,
    get_or_create_global_room,
    is_room_participant,
)
from app.utils.decorators import active_user_required, csrf_required, login_required
from app.utils.security import error_response, get_client_ip, sanitize_text, success_response

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/rooms/global/messages", methods=["GET"])
@login_required
@active_user_required
def get_global_messages(user):
    room = ensure_global_participant(user.id)
    messages = (
        ChatMessage.query.filter_by(room_id=room.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(100)
        .all()
    )
    messages.reverse()
    return success_response([m.to_dict() for m in messages])


@chat_bp.route("/rooms/global/messages", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def send_global_message(user):
    data = request.get_json(silent=True) or {}
    content = sanitize_text(data.get("content"), 500)
    if not content:
        return error_response("메시지를 입력해주세요.", 400)

    room = ensure_global_participant(user.id)
    message = ChatMessage(room_id=room.id, sender_id=user.id, content=content)
    db.session.add(message)
    db.session.commit()

    msg_dict = message.to_dict()
    socketio.emit("global_message", msg_dict, room=f"global_{room.id}")

    log_event(user.id, "CHAT_GLOBAL", f"room_id={room.id}", get_client_ip())
    return success_response(msg_dict, "메시지가 전송되었습니다.", 201)


@chat_bp.route("/rooms/direct", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def create_direct_room(user):
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")
    product_id = data.get("product_id")

    try:
        target_user_id = int(target_user_id)
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("대상 사용자 ID가 올바르지 않습니다.", 400)

    target = User.query.get(target_user_id)
    if not target or target.status == "DELETED":
        return error_response("대상 사용자를 찾을 수 없습니다.", 404)

    product = Product.query.get(product_id)
    if not product or product.status != "ACTIVE":
        return error_response("상품을 찾을 수 없습니다.", 404)
    if product.seller_id != target_user_id:
        return error_response("상품 판매자와 대화 상대가 일치하지 않습니다.", 400)

    room = get_or_create_direct_room(user.id, target_user_id, product_id)
    if not room:
        return error_response("자기 자신과는 채팅할 수 없습니다.", 400)

    return success_response({"room_id": room.id, "target_user": target.to_public_dict()})


@chat_bp.route("/rooms/direct", methods=["GET"])
@login_required
@active_user_required
def list_direct_rooms(user):
    """Return the current user's direct-message inbox."""
    rooms = (
        ChatRoom.query.filter_by(room_type="DIRECT")
        .join(ChatParticipant)
        .filter(ChatParticipant.user_id == user.id)
        .order_by(ChatRoom.created_at.desc())
        .all()
    )

    items = []
    for room in rooms:
        other_participant = ChatParticipant.query.filter(
            ChatParticipant.room_id == room.id,
            ChatParticipant.user_id != user.id,
        ).first()
        if not other_participant:
            continue

        items.append(
            {
                "room_id": room.id,
                "other_user": other_participant.user.to_public_dict(),
                "product": room.product.to_list_dict() if room.product else None,
            }
        )

    return success_response(items)


@chat_bp.route("/rooms/<int:room_id>/messages", methods=["GET"])
@login_required
@active_user_required
def get_room_messages(user, room_id):
    if not is_room_participant(room_id, user.id) and not user.is_admin():
        log_event(user.id, "IDOR_ATTEMPT", f"chat_room_id={room_id}", get_client_ip())
        return error_response("채팅방 접근 권한이 없습니다.", 403)

    messages = (
        ChatMessage.query.filter_by(room_id=room_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(100)
        .all()
    )
    messages.reverse()
    return success_response([m.to_dict() for m in messages])


@chat_bp.route("/rooms/<int:room_id>/messages", methods=["POST"])
@login_required
@csrf_required
@active_user_required
def send_room_message(user, room_id):
    if not is_room_participant(room_id, user.id):
        log_event(user.id, "IDOR_ATTEMPT", f"chat_room_id={room_id}", get_client_ip())
        return error_response("채팅방 접근 권한이 없습니다.", 403)

    data = request.get_json(silent=True) or {}
    content = sanitize_text(data.get("content"), 500)
    if not content:
        return error_response("메시지를 입력해주세요.", 400)

    message = ChatMessage(room_id=room_id, sender_id=user.id, content=content)
    db.session.add(message)
    db.session.commit()

    msg_dict = message.to_dict()
    socketio.emit("direct_message", msg_dict, room=f"direct_{room_id}")

    log_event(user.id, "CHAT_DIRECT", f"room_id={room_id}", get_client_ip())
    return success_response(msg_dict, "메시지가 전송되었습니다.", 201)
