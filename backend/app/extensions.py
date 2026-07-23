from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

blocklist = set()  # 실서비스는 Redis 권장

@jwt.token_in_blocklist_loader
def check_if_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blocklist

# auth.py logout()
from flask_jwt_extended import get_jwt
blocklist.add(get_jwt()["jti"])
