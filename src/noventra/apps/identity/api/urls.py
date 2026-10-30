"""Identity API URLs — authN endpoints."""

from django.urls import path

from .views import LoginView, RefreshView, LogoutView, SwitchTenantView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("switch-tenant/", SwitchTenantView.as_view(), name="auth-switch-tenant"),
]
