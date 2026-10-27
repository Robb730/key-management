from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import role_required
from .models import AuditLog


@role_required("ADMIN")
def audit_log(request):
    """Read-only audit log. Admin-only. Filterable by user, action type,
    model and date range; paginated because this table grows fast."""
    qs = AuditLog.objects.select_related("user").all()

    user_id = request.GET.get("user", "").strip()
    action = request.GET.get("action", "").strip()
    model_name = request.GET.get("model", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if user_id:
        qs = qs.filter(user_id=user_id)
    if action:
        qs = qs.filter(action=action)
    if model_name:
        qs = qs.filter(model__icontains=model_name)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "users": AuditLog.objects.values_list("user", flat=True).distinct(),
        "actions": AuditLog.Action.choices,
        "models": AuditLog.objects.values_list("model", flat=True)
            .exclude(model="").distinct(),
        "filter_user": user_id,
        "filter_action": action,
        "filter_model": model_name,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
    }
    return render(request, "audit/audit_log.html", context)
