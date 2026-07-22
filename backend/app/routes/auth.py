from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.services.audit_service import log_event
from app.services.chat_service import create_csrf_token
from app.utils.decorators import csrf_required, login_required
from app.utils.security import (
    EMAIL_PATTERN,
    PHONE_PATTERN,
    USERNAME_PATTERN,
    error_response,
    get_client_ip,
    hash_password,
    is_account_locked,
    lock_account,
    reset_login_attempts,
    success_response,
    validate_password,
    verify_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    nickname = (data.get("nickname") or username).strip()

    if not all([username, password, email, phone]):
        return error_response("아이디, 비밀번호, 이메일, 전화번호는 필수입니다.", 400)

    if not USERNAME_PATTERN.match(username):
        return error_response("아이디는 4~20자의 영문, 숫자, 밑줄만 사용 가능합니다.", 400)

    if not EMAIL_PATTERN.match(email):
        return error_response("올바른 이메일 형식이 아닙니다.", 400)

    if not PHONE_PATTERN.match(phone):
        return error_response("올바른 전화번호 형식이 아닙니다.", 400)

    valid, msg = validate_password(password)
    if not valid:
        return error_response(msg, 400)

    if User.query.filter_by(username=username).first():
        return error_response("이미 사용 중인 아이디입니다.", 409)

    if User.query.filter_by(email=email).first():
        return error_response("이미 사용 중인 이메일입니다.", 409)

    user = User(
        username=username,
        email=email,
        phone=phone,
        nickname=nickname[:50],
        password_hash=hash_password(password),
        balance=current_app.config["INITIAL_USER_BALANCE"],
    )
    db.session.add(user)
    db.session.commit()

    log_event(user.id, "SIGNUP", f"username={username}", get_client_ip())
    return success_response({"user_id": user.id}, "회원가입이 완료되었습니다.", 201)


@auth_bp.route("/check-email", methods=["GET"])
def check_email():
    email = (request.args.get("email") or "").strip()
    if not email or not EMAIL_PATTERN.match(email):
        return error_response("올바른 이메일 형식이 아닙니다.", 400)

    exists = User.query.filter_by(email=email).first() is not None
    return success_response({"available": not exists})


@auth_bp.route("/check-username", methods=["GET"])
def check_username():
    username = (request.args.get("username") or "").strip()
    if not username or not USERNAME_PATTERN.match(username):
        return error_response("올바른 아이디 형식이 아닙니다.", 400)

    exists = User.query.filter_by(username=username).first() is not None
    return success_response({"available": not exists})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error_response("아이디와 비밀번호를 입력해주세요.", 400)

    user = User.query.filter_by(username=username).first()
    if not user:
        log_event(None, "LOGIN_FAILED", f"username={username}", get_client_ip())
        return error_response("아이디 또는 비밀번호가 올바르지 않습니다.", 401)

    if user.status == "DELETED":
        return error_response("삭제된 계정입니다.", 403)

    if is_account_locked(user):
        db.session.commit()
        return error_response("로그인 시도 횟수를 초과하여 계정이 잠겼습니다. 10분 후 다시 시도해주세요.", 429)

    if not verify_password(password, user.password_hash):
        user.login_attempts += 1
        if user.login_attempts >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
            lock_account(user)
            db.session.commit()
            log_event(user.id, "ACCOUNT_LOCKED", f"username={username}", get_client_ip())
            return error_response("로그인 시도 횟수를 초과하여 계정이 10분간 잠겼습니다.", 429)
        db.session.commit()
        log_event(user.id, "LOGIN_FAILED", f"username={username}", get_client_ip())
        return error_response("아이디 또는 비밀번호가 올바르지 않습니다.", 401)

    reset_login_attempts(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    csrf_token = create_csrf_token(user.id)

    log_event(user.id, "LOGIN_SUCCESS", f"username={username}", get_client_ip())

    return success_response(
        {
            "access_token": access_token,
            "csrf_token": csrf_token,
            "user": user.to_private_dict(),
        },
        "로그인 성공",
    )


@auth_bp.route("/logout", methods=["POST"])
@login_required
@csrf_required
def logout(user):
    from app.models.csrf_token import CsrfToken

    CsrfToken.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    log_event(user.id, "LOGOUT", None, get_client_ip())
    return success_response(message="로그아웃 되었습니다.")
