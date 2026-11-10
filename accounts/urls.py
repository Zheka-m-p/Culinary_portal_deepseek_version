from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Свой профиль. ОБЯЗАТЕЛЬНО должен идти ДО маршрута с <username>/,
    # иначе "profile" будет пойман как username и уйдет в чужой профиль.
    path("profile/", views.ProfileView.as_view(), name="profile"),

    # Чужой профиль по username
    path("profile/<str:username>/", views.ProfileView.as_view(), name="profile_detail"),
]