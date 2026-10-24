from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import AuditLogModel, PolicyDecision

SENSITIVE_FIELD_NAMES = {
    "password", "secret", "token", "auth", "key", "api_key",
    "db_admin_password", "credential", "private_key", "bearer"
}


def sanitize_payload(obj: Any) -> Any:
    """
    Recursively scrubs secrets and passwords from arguments before audit persistence.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in SENSITIVE_FIELD_NAMES):
                cleaned[k] = "[REDACTED_SECRET]"
            elif isinstance(v, (dict, list)):
                cleaned[k] = sanitize_payload(v)
            elif isinstance(v, str) and any(s in v.lower() for s in ["supersecret", "sk_live"]):
                cleaned[k] = "[REDACTED_SECRET_STRING]"
            else:
                cleaned[k] = v
        return cleaned
    elif isinstance(obj, list):
        return [sanitize_payload(x) for x in obj]
    return obj


class AuditLogger:
    @staticmethod
    def log_tool_decision(
        db: Session,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        decision: PolicyDecision,
        reason_code: str,
        reason_description: str,
        was_executed: bool,
        execution_result: Optional[Dict[str, Any]],
        error_message: Optional[str],
        latency_ms: float,
        user_role: str,
        access_strategy: str,
        model: str
    ) -> AuditLogModel:
        sanitized_args = sanitize_payload(arguments)
        sanitized_res = sanitize_payload(execution_result) if execution_result else None

        entry = AuditLogModel(
            task_id=task_id,
            timestamp=datetime.now(timezone.utc),
            tool_name=tool_name,
            sanitized_arguments=sanitized_args,
            policy_decision=decision,
            reason_code=reason_code,
            reason_description=reason_description,
            was_executed=was_executed,
            execution_result=sanitized_res,
            error_message=error_message,
            latency_ms=round(latency_ms, 2),
            user_role=user_role,
            access_strategy=access_strategy,
            model=model
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
