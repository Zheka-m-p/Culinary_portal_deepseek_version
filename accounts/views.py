from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from recipes.models import Recipe
from .forms import LoginForm, RegistrationForm
from .models import User


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


class LogoutView(DjangoLogoutView):
    """Выход. В Django 5.0+ работает ТОЛЬКО через POST (защита от CSRF-атак через GET)."""

    next_page = reverse_lazy("recipes:recipe_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Вы вышли из аккаунта.")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(ListView):
    """Профиль пользователя.

    Одна вьюха на два случая:
    - /accounts/profile/             → свой профиль (требует логина)
    - /accounts/profile/<username>/  → чужой публичный профиль (только опубликованное)

    Разделение делает get_target_user(): если в URL есть username — берём его,
    иначе берём request.user.
    """

    template_name = "accounts/profile.html"
    context_object_name = "recipes"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        """Свой профиль требует логина. Чужой — публичный."""
        # Если нет username в URL и юзер не залогинен — отправляем на логин
        if not kwargs.get("username") and not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def get_target_user(self):
        """Чей профиль показываем: свой или чужой по username из URL."""
        username = self.kwargs.get("username")
        if username:
            # iexact — регистронезависимый поиск (Ivan = ivan)
            return get_object_or_404(User, username__iexact=username)
        return self.request.user

    def get_queryset(self):
        """Список рецептов этого юзера с учётом видимости."""
        target_user = self.get_target_user()
        is_own = target_user == self.request.user

        qs = Recipe.objects.filter(author=target_user).select_related("category")

        # Чужой профиль — только опубликованные (черновики чужих не видим никому)
        if not is_own:
            return qs.filter(is_published=True).order_by("-created_at")

        # Свой профиль — табы. По умолчанию "all"
        tab = self.request.GET.get("tab", "all")
        if tab == "published":
            qs = qs.filter(is_published=True)
        elif tab == "drafts":
            qs = qs.filter(is_published=False)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        """Счётчики для карточки юзера и активный таб."""
        context = super().get_context_data(**kwargs)
        target_user = self.get_target_user()
        is_own = target_user == self.request.user

        all_recipes = Recipe.objects.filter(author=target_user)

        context["profile_user"] = target_user
        context["is_own_profile"] = is_own

        if is_own:
            # Автор видит полную статистику
            context["total_count"] = all_recipes.count()
            context["published_count"] = all_recipes.filter(is_published=True).count()
            context["drafts_count"] = all_recipes.filter(is_published=False).count()
            context["current_tab"] = self.request.GET.get("tab", "all")
        else:
            # Чужие видят только опубликованные. Общее количество приравниваем к опубликованным,
            # чтобы никто не догадался, сколько у автора черновиков.
            published_count = all_recipes.filter(is_published=True).count()
            context["total_count"] = published_count
            context["published_count"] = published_count
            context["drafts_count"] = 0
            context["current_tab"] = "published"

        return context