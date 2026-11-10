from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, RegistrationForm

class RegisterView(CreateView):
    """Регистрация нового пользователя.

    Используем CreateView, потому что он уже умеет:
    - рендерить форму (GET)
    - принимать данные и валидировать (POST)
    - показывать ошибки формы, если что-то не так
    - редиректить на success_url после успеха

    Наша задача — передать ему форму, шаблон и в form_valid() залогинить юзера.
    """

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("recipes:recipe_list")

    def dispatch(self, request, *args, **kwargs):
        """Если юзер уже залогинен — ему нечего делать на странице регистрации."""
        if request.user.is_authenticated:
            messages.info(request, "Вы уже авторизованы.")
            return redirect("recipes:recipe_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Форма валидна: сохраняем юзера и сразу логиним его.

        form.save() вернёт объект User (с захэшированным паролем — спасибо UserCreationForm).
        Затем login(self.request, user) создаст сессию, и юзер сразу окажется авторизован.
        Это лучше, чем редиректить на страницу логина и заставлять вводить пароль ещё раз.
        """
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Добро пожаловать, {self.object.username}! Аккаунт успешно создан.",
        )
        return response


class LoginView(DjangoLoginView):
    """Вход. Оборачиваем стандартный LoginView, чтобы подставить нашу форму и шаблон."""

    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True  # если уже залогинен — на главную, без формы

    def form_valid(self, form):
        """Стандартный form_valid уже вызывает auth_login(). Добавляем только сообщение."""
        response = super().form_valid(form)
        messages.success(self.request, f"С возвращением, {self.request.user.username}!")
        return response

    def form_invalid(self, form):
        """Ошибка входа (неверный логин/пароль)."""
        messages.error(self.request, "Неверный email/логин или пароль.")
        return super().form_invalid(form)

    def get_success_url(self):
        """Куда редиректить после логина.

        По умолчанию Django возьмёт LOGIN_REDIRECT_URL из settings.py (мы зададим "/").
        Но если юзер пришёл по ссылке вида /accounts/login/?next=/recipes/xxx/update/,
        (например, аноним попытался зайти в CRUD), то Django сам редиректнет его туда.
        """
        return super().get_success_url()


class LogoutView(DjangoLogoutView):
    """Выход. В Django 5.0+ работает ТОЛЬКО через POST (защита от CSRF-атак через GET)."""

    next_page = reverse_lazy("recipes:recipe_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Вы вышли из аккаунта.")
        return super().dispatch(request, *args, **kwargs)