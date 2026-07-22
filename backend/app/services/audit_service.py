from app.extensions import db
from app.models.audit_log import AuditLog


def log_event(user_id, action, details=None, ip_address=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    db.session.add(log)
    db.session.commit()
