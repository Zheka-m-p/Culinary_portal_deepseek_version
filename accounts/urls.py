from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # ВАЖНО: profile/edit/ ДОЛЖЕН идти строго ДО profile/<username>/
    # Иначе "edit" будет пойман как username, и мы получим 404.
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/<str:username>/", views.ProfileView.as_view(), name="profile_detail"),
]