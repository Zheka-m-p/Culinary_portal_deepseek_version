from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, ListView, UpdateView

from recipes.models import Recipe
from .forms import LoginForm, ProfileUpdateForm, RegistrationForm
from .models import User


class RegisterView(CreateView):
    """Регистрация нового пользователя."""

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("recipes:recipe_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Вы уже авторизованы.")
            return redirect("recipes:recipe_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Добро пожаловать, {self.object.username}! Аккаунт успешно создан.",
        )
        return response

    def get_success_url(self):
        """После регистрации идём туда, куда шёл юзер (?next=), если ссылка безопасна.

        url_has_allowed_host_and_scheme — защита от open redirect:
        без неё ?next=https://evil.com увёл бы юзера на фишинг.
        """
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return super().get_success_url()


class LoginView(DjangoLoginView):
    """Вход. Django из коробки понимает ?next= (проверенный)."""
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"С возвращением, {self.request.user.username}!")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Неверный email/логин или пароль.")
        return super().form_invalid(form)


class LogoutView(DjangoLogoutView):
    """Выход."""
    next_page = reverse_lazy("recipes:recipe_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Вы вышли из аккаунта.")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(ListView):
    """Профиль пользователя."""
    template_name = "accounts/profile.html"
    context_object_name = "recipes"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        if not kwargs.get("username") and not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def get_target_user(self):
        username = self.kwargs.get("username")
        if username:
            return get_object_or_404(User, username__iexact=username)
        return self.request.user

    def get_queryset(self):
        target_user = self.get_target_user()
        is_own = target_user == self.request.user
        qs = Recipe.objects.filter(author=target_user).select_related("category")

        if not is_own:
            return qs.filter(is_published=True).order_by("-created_at")

        tab = self.request.GET.get("tab", "all")
        if tab == "published":
            qs = qs.filter(is_published=True)
        elif tab == "drafts":
            qs = qs.filter(is_published=False)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.get_target_user()
        is_own = target_user == self.request.user
        all_recipes = Recipe.objects.filter(author=target_user)

        context["profile_user"] = target_user
        context["is_own_profile"] = is_own

        if is_own:
            context["total_count"] = all_recipes.count()
            context["published_count"] = all_recipes.filter(is_published=True).count()
            context["drafts_count"] = all_recipes.filter(is_published=False).count()
            context["current_tab"] = self.request.GET.get("tab", "all")
        else:
            published_count = all_recipes.filter(is_published=True).count()
            context["total_count"] = published_count
            context["published_count"] = published_count
            context["drafts_count"] = 0
            context["current_tab"] = "published"

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование своего профиля."""
    model = User
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Профиль успешно обновлён.")
        return response