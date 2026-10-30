"""Audit API URLs."""

from django.urls import path

from .views import AuditLogView

urlpatterns = [
    path("log/", AuditLogView.as_view(), name="audit-log-read"),
]
