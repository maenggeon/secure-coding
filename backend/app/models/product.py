from datetime import datetime, timezone

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), default="ACTIVE", nullable=False, index=True)
    report_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_list_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "image_path": self.image_path,
            "status": self.status,
            "seller_id": self.seller_id,
            "seller_nickname": self.seller.nickname if self.seller else None,
        }

    def to_detail_dict(self):
        data = self.to_list_dict()
        data.update(
            {
                "description": self.description,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "seller": {
                    "id": self.seller.id,
                    "username": self.seller.username,
                    "nickname": self.seller.nickname,
                }
                if self.seller
                else None,
            }
        )
        return data
