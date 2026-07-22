from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text, default="")
    role = db.Column(db.String(20), default="USER", nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default="ACTIVE", nullable=False)
    login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", backref="seller", lazy="dynamic")
    sent_transactions = db.relationship(
        "Transaction", foreign_keys="Transaction.sender_id", backref="sender", lazy="dynamic"
    )
    received_transactions = db.relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", backref="receiver", lazy="dynamic"
    )

    def is_admin(self):
        return self.role == "ADMIN"

    def is_blocked(self):
        return self.status in ("SUSPENDED", "BLOCKED")

    def to_public_dict(self, include_products=False):
        data = {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_products:
            data["products"] = [
                p.to_list_dict() for p in self.products.filter_by(status="ACTIVE").all()
            ]
        return data

    def to_private_dict(self):
        data = self.to_public_dict()
        data.update(
            {
                "email": self.email,
                "phone": self.phone,
                "balance": self.balance,
                "role": self.role,
                "status": self.status,
            }
        )
        return data
