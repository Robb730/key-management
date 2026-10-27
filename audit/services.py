"""Helpers for writing audit log entries."""

from django.utils import timezone

from .models import AuditLog


def log_action(*, action, user=None, model="", object_id="", object_repr="",
               message="", ip_address=None):
    """Create a read-only audit log entry.

    All arguments are keyword-only. Fail-safe: never raises so calling code
    can't break the main request flow if the audit write hiccups.
    """
    try:
        AuditLog.objects.create(
            action=action,
            user=user,
            model=model,
            object_id=str(object_id)[:50] if object_id else "",
            object_repr=object_repr[:255],
            message=message,
            ip_address=ip_address,
            created_at=timezone.now(),
        )
    except Exception:
        # Audit logging must never break the request/response cycle.
        pass
