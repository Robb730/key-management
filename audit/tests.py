from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from audit.models import AuditLog

User = get_user_model()


class AuditLogViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass1234",
            role="ADMIN", approval_status=User.Approval.APPROVED)
        self.guard = User.objects.create_user(
            username="guard", email="guard@example.com", password="pass1234",
            role="GUARD", approval_status=User.Approval.APPROVED)

        for i in range(30):
            AuditLog.objects.create(
                action=AuditLog.Action.KEY_BORROW if i % 2 == 0 else AuditLog.Action.KEY_RETURN,
                user=self.admin if i % 3 == 0 else self.guard,
                model="Key",
                object_id=str(i),
                object_repr=f"K{i:03d} (RM101)",
                message=f"Test entry {i}",
                ip_address="127.0.0.1",
            )

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        url = reverse("audit:audit_log")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Audit Log")
        self.assertTrue(resp.context["page_obj"].has_other_pages())
        # first page shows 25 of 30
        self.assertEqual(len(resp.context["page_obj"]), 25)

    def test_guard_cannot_view(self):
        self.client.force_login(self.guard)
        resp = self.client.get(reverse("audit:audit_log"))
        # role_required raises PermissionDenied -> 403
        self.assertEqual(resp.status_code, 403)

    def test_filter_by_action(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("audit:audit_log") + "?action=KEY_RETURN")
        self.assertEqual(resp.status_code, 200)
        for entry in resp.context["page_obj"]:
            self.assertEqual(entry.action, "KEY_RETURN")

    def test_filter_by_user(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("audit:audit_log") + f"?user={self.guard.pk}")
        self.assertEqual(resp.status_code, 200)
        for entry in resp.context["page_obj"]:
            self.assertEqual(entry.user, self.guard)

    def test_filter_by_date(self):
        self.client.force_login(self.admin)
        today = timezone.localdate().isoformat()
        resp = self.client.get(
            reverse("audit:audit_log") + f"?date_from={today}&date_to={today}")
        self.assertEqual(resp.status_code, 200)

    def test_filter_preserved_in_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("audit:audit_log") + "?action=KEY_BORROW")
        self.assertEqual(resp.status_code, 200)
        # the chosen action stays selected in the form
        self.assertContains(resp, 'value="KEY_BORROW" selected')

    def test_pagination_links_preserve_filters(self):
        # enough borrow entries to span two pages so pagination links exist
        for i in range(30):
            AuditLog.objects.create(
                action=AuditLog.Action.KEY_BORROW, user=self.admin,
                model="Key", object_id=str(100 + i), object_repr=f"X{i}",
                message="extra", ip_address="127.0.0.1")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("audit:audit_log") + "?action=KEY_BORROW&page=2")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "action=KEY_BORROW")
