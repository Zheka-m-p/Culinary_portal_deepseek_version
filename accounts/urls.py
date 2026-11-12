from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Активация email
    path("activate/<str:token>/", views.ActivateView.as_view(), name="activate"),
    path(
        "activation-sent/",
        TemplateView.as_view(template_name="accounts/activation_sent.html"),
        name="activation_sent",
    ),
    path("resend-activation/", views.ResendActivationView.as_view(), name="resend_activation"),

    # Профиль
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/<str:username>/", views.ProfileView.as_view(), name="profile_detail"),

    # Смена пароля (для залогиненных)
    path("password/change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),

    # Восстановление пароля (для тех, кто забыл)
    path("password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "password/reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]