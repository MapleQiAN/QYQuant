from ..extensions import db
from ..models import AuditLog


def log_audit(operator_id, action, target_type, target_id, details=None):
    audit = AuditLog(
        operator_id=operator_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    db.session.add(audit)
    return audit


def write_audit_log(operator_id, action, target_type, target_id, details=None):
    audit = log_audit(
        operator_id=operator_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.session.commit()
    return audit
