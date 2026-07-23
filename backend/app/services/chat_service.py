from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.chat import ChatRoom, ChatParticipant
from app.models.csrf_token import CsrfToken
from app.models.user import User
from app.utils.security import generate_csrf_token


def create_csrf_token(user_id):
    CsrfToken.query.filter_by(user_id=user_id).delete()
    token = generate_csrf_token()
    csrf = CsrfToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.session.add(csrf)
    db.session.commit()
    return token


def get_or_create_global_room():
    room = ChatRoom.query.filter_by(room_type="GLOBAL").first()
    if not room:
        room = ChatRoom(room_type="GLOBAL")
        db.session.add(room)
        db.session.commit()
    return room


def get_or_create_direct_room(user1_id, user2_id, product_id):
    if user1_id == user2_id:
        return None

    rooms = (
        db.session.query(ChatRoom)
        .filter(ChatRoom.room_type == "DIRECT", ChatRoom.product_id == product_id)
        .join(ChatParticipant)
        .filter(ChatParticipant.user_id.in_([user1_id, user2_id]))
        .all()
    )

    for room in rooms:
        participant_ids = {p.user_id for p in room.participants.all()}
        if participant_ids == {user1_id, user2_id}:
            return room

    room = ChatRoom(room_type="DIRECT", product_id=product_id)
    db.session.add(room)
    db.session.flush()
    db.session.add(ChatParticipant(room_id=room.id, user_id=user1_id))
    db.session.add(ChatParticipant(room_id=room.id, user_id=user2_id))
    db.session.commit()
    return room


def is_room_participant(room_id, user_id):
    return (
        ChatParticipant.query.filter_by(room_id=room_id, user_id=user_id).first() is not None
    )


def ensure_global_participant(user_id):
    room = get_or_create_global_room()
    existing = ChatParticipant.query.filter_by(room_id=room.id, user_id=user_id).first()
    if not existing:
        db.session.add(ChatParticipant(room_id=room.id, user_id=user_id))
        db.session.commit()
    return room
