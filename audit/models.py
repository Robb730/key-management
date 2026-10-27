from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable, read-only audit trail of security-relevant actions.

    Intended for admins/auditors only. Entries are written by the
    application (see audit.services.log_action) and never edited here.
    """

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        KEY_CREATE = "KEY_CREATE", "Key Created"
        KEY_UPDATE = "KEY_UPDATE", "Key Updated"
        KEY_BORROW = "KEY_BORROW", "Key Borrowed"
        KEY_RETURN = "KEY_RETURN", "Key Returned"
        BORROWER_CREATE = "BORROWER_CREATE", "Borrower Created"
        BORROWER_UPDATE = "BORROWER_UPDATE", "Borrower Updated"
        BORROWER_TOGGLE = "BORROWER_TOGGLE", "Borrower Activated/Deactivated"
        SHIFT_START = "SHIFT_START", "Shift Started"
        SHIFT_END = "SHIFT_END", "Shift Ended"
        SETTINGS_UPDATE = "SETTINGS_UPDATE", "Settings Updated"

    # Lucide icon name + Tailwind colour per action type.
    _ACTION_META = {
        Action.LOGIN: ("log-in", "bg-blue-50 text-blue-700 border-blue-100"),
        Action.LOGOUT: ("log-out", "bg-stone-50 text-stone-700 border-stone-100"),
        Action.KEY_CREATE: ("plus-circle", "bg-green-50 text-green-700 border-green-100"),
        Action.KEY_UPDATE: ("edit-3", "bg-amber-50 text-amber-700 border-amber-100"),
        Action.KEY_BORROW: ("arrow-right", "bg-blue-50 text-blue-700 border-blue-100"),
        Action.KEY_RETURN: ("arrow-left", "bg-green-50 text-green-700 border-green-100"),
        Action.BORROWER_CREATE: ("user-plus", "bg-indigo-50 text-indigo-700 border-indigo-100"),
        Action.BORROWER_UPDATE: ("edit-3", "bg-amber-50 text-amber-700 border-amber-100"),
        Action.BORROWER_TOGGLE: ("toggle-right", "bg-purple-50 text-purple-700 border-purple-100"),
        Action.SHIFT_START: ("clock", "bg-teal-50 text-teal-700 border-teal-100"),
        Action.SHIFT_END: ("clock", "bg-red-50 text-red-700 border-red-100"),
        Action.SETTINGS_UPDATE: ("settings", "bg-stone-50 text-stone-700 border-stone-100"),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    model = models.CharField(max_length=50, blank=True, db_index=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        verbose_name = "audit log entry"
        verbose_name_plural = "audit log entries"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.get_action_display()} by {self.user or 'system'}"

    @property
    def icon(self):
        return self._ACTION_META[self.action][0]

    @property
    def badge_classes(self):
        return self._ACTION_META[self.action][1]
