from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models.csrf_token import CsrfToken
from app.models.user import User
from app.utils.security import as_utc, error_response, get_client_ip
from datetime import datetime, timezone


def get_current_user():
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return error_response("사용자를 찾을 수 없습니다.", 401)
        if user.status == "DELETED":
            return error_response("삭제된 계정입니다.", 403)
        return fn(user, *args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_admin():
            from app.services.audit_service import log_event

            log_event(None, "UNAUTHORIZED_ADMIN_ACCESS", f"user_id={user_id}", get_client_ip())
            return error_response("관리자 권한이 필요합니다.", 403)
        return fn(user, *args, **kwargs)

    return wrapper


def active_user_required(fn):
    @wraps(fn)
    def wrapper(user, *args, **kwargs):
        if user.is_blocked():
            return error_response("제재된 계정은 이 기능을 사용할 수 없습니다.", 403)
        return fn(user, *args, **kwargs)

    return wrapper


def csrf_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        token = request.headers.get("X-CSRF-Token")
        if not token:
            return error_response("CSRF 토큰이 필요합니다.", 403)

        csrf = CsrfToken.query.filter_by(user_id=user_id, token=token).first()
        if not csrf or as_utc(csrf.expires_at) < datetime.now(timezone.utc):
            return error_response("유효하지 않은 CSRF 토큰입니다.", 403)
        return fn(*args, **kwargs)

    return wrapper
