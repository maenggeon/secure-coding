from datetime import datetime, timezone

from app.extensions import db


class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_type = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    participants = db.relationship("ChatParticipant", backref="room", lazy="dynamic")
    messages = db.relationship("ChatMessage", backref="room", lazy="dynamic")


class ChatParticipant(db.Model):
    __tablename__ = "chat_participants"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref="chat_participations")

    __table_args__ = (db.UniqueConstraint("room_id", "user_id", name="uq_room_user"),)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship("User", backref="chat_messages")

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "sender_id": self.sender_id,
            "sender_nickname": self.sender.nickname if self.sender else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
