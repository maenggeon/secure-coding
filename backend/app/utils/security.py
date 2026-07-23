import hashlib
import io
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from PIL import Image
from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename

PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,24}$"
    r"|^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,24}$"
    r"|^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,24}$"
    r"|^(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,24}$"
    r"|^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,24}$"
)

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{4,20}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$")


def validate_password(password):
    if not password or len(password) < 8 or len(password) > 24:
        return False, "비밀번호는 8~24자여야 합니다."

    categories = 0
    if re.search(r"[a-z]", password):
        categories += 1
    if re.search(r"[A-Z]", password):
        categories += 1
    if re.search(r"\d", password):
        categories += 1
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        categories += 1

    if categories < 3:
        return False, "비밀번호는 영문 대/소문자, 숫자, 특수문자 중 3종류 이상을 포함해야 합니다."
    return True, ""


def hash_password(password):
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return f"{salt.hex()}${pwd_hash.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
        return secrets.compare_digest(pwd_hash.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def generate_csrf_token():
    return secrets.token_urlsafe(32)


def success_response(data=None, message="성공", status=200):
    return jsonify({"success": True, "data": data, "message": message}), status


def error_response(message="오류가 발생했습니다.", status=400):
    return jsonify({"success": False, "message": message}), status


def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "unknown"


def allowed_file(filename, mimetype):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return False
    if mimetype not in current_app.config["ALLOWED_MIME_TYPES"]:
        return False
    return True


def save_product_image(file):
    if not file or file.filename == "":
        return None, None
    if not allowed_file(file.filename, file.mimetype):
        return None, "허용되지 않는 파일 형식입니다."

    raw = file.read()
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()                     # 실제 이미지 구조 검증
        img = Image.open(io.BytesIO(raw))
        if img.format.lower() not in {"png", "jpeg", "gif", "webp"}:
            return None, "허용되지 않는 파일 형식입니다."
    except Exception:
        return None, "손상되었거나 유효하지 않은 이미지 파일입니다."

    filename = secure_filename(file.filename)
    unique_name = f"{secrets.token_hex(16)}_{filename}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    # 원본 대신 재인코딩해서 저장 → 메타데이터/페이로드 제거
    img.save(filepath)
    return unique_name, None


def sanitize_text(text, max_length=1000):
    if text is None:
        return ""
    text = str(text).strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


def as_utc(value):
    """Treat database datetimes without timezone data as UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def is_account_locked(user):
    locked_until = as_utc(user.locked_until)
    if locked_until and locked_until > datetime.now(timezone.utc):
        return True
    if locked_until and locked_until <= datetime.now(timezone.utc):
        user.login_attempts = 0
        user.locked_until = None
    return False


def lock_account(user):
    user.login_attempts = current_app.config["LOGIN_MAX_ATTEMPTS"]
    user.locked_until = datetime.now(timezone.utc) + timedelta(
        minutes=current_app.config["LOGIN_LOCKOUT_MINUTES"]
    )


def reset_login_attempts(user):
    user.login_attempts = 0
    user.locked_until = None

