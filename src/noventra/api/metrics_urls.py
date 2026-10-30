"""Metrics endpoint URLs."""

from django.urls import path

from .metrics import MetricsView

urlpatterns = [
    path("", MetricsView.as_view(), name="metrics"),
]
