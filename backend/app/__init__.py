import os

from flask import send_from_directory
from flask_cors import CORS
from sqlalchemy import text

from app.config import Config
from app.extensions import db, jwt, socketio
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.chat import chat_bp
from app.routes.products import products_bp
from app.routes.reports import reports_bp
from app.routes.transactions import transactions_bp
from app.routes.users import users_bp
from app.services.chat_service import get_or_create_global_room
from app.utils.security import hash_password


def create_app(config_class=Config):
    from flask import Flask

    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    @app.route("/api/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(404)
    def not_found(e):
        from app.utils.security import error_response

        return error_response("요청한 리소스를 찾을 수 없습니다.", 404)

    @app.errorhandler(500)
    def internal_error(e):
        from app.utils.security import error_response

        db.session.rollback()
        return error_response("서버 내부 오류가 발생했습니다.", 500)

    @app.errorhandler(413)
    def too_large(e):
        from app.utils.security import error_response

        return error_response("파일 크기가 너무 큽니다. (최대 5MB)", 413)

    with app.app_context():
        db.create_all()
        if db.engine.dialect.name == "postgresql":
            db.session.execute(
                text(
                    "ALTER TABLE chat_rooms "
                    "ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id)"
                )
            )
            db.session.commit()
        _seed_admin(app)
        get_or_create_global_room()

    register_socketio_events()

    return app


def _seed_admin(app):
    from app.models.user import User

    admin = User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first()
    if not admin:
        admin = User(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            phone="010-0000-0000",
            nickname="관리자",
            password_hash=hash_password(app.config["ADMIN_PASSWORD"]),
            role="ADMIN",
            balance=0,
        )
        db.session.add(admin)
        db.session.commit()


def register_socketio_events():
    from flask import request
    from flask_jwt_extended import decode_token

    from app.services.chat_service import is_room_participant

    @socketio.on("join_global")
    def on_join_global(data):
        try:
            token = data.get("token")
            decoded = decode_token(token)
            user_id = int(decoded["sub"])
            room = get_or_create_global_room()
            from flask_socketio import join_room

            join_room(f"global_{room.id}")
        except Exception:
            pass

    @socketio.on("join_direct")
    def on_join_direct(data):
        try:
            token = data.get("token")
            room_id = data.get("room_id")
            decoded = decode_token(token)
            user_id = int(decoded["sub"])
            if is_room_participant(room_id, user_id):
                from flask_socketio import join_room

                join_room(f"direct_{room_id}")
        except Exception:
            pass
