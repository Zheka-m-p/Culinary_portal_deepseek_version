from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from recipes.models import Recipe
from .forms import LoginForm, ProfileUpdateForm, RegistrationForm
from .models import User
from .tokens import verify_token
from .utils import send_activation_email


class RegisterView(CreateView):
    """Регистрация с подтверждением email."""

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:activation_sent")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Вы уже авторизованы.")
            return redirect("recipes:recipe_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Создаём юзера, но НЕ активного — активируется после клика в письме
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.save()

        # Отправляем письмо со ссылкой активации
        send_activation_email(self.request, self.object)

        messages.success(
            self.request,
            f"Аккаунт создан! Мы отправили письмо на {self.object.email}. "
            f"Перейдите по ссылке из письма, чтобы активировать его.",
        )
        # Наследуем поведение CreateView: редирект на success_url
        return redirect(self.get_success_url())


class ActivateView(View):
    """Приём токена из письма, активация юзера."""

    def get(self, request, token):
        pk = verify_token(token)
        if pk is None:
            # Токен подделан или истёк
            return render(request, "accounts/activation_invalid.html")

        user = get_object_or_404(User, pk=pk)
        if user.is_active:
            messages.info(request, "Аккаунт уже активирован. Можете войти.")
        else:
            user.is_active = True
            user.save()
            messages.success(request, "Аккаунт успешно активирован! Теперь вы можете войти.")
        return redirect("accounts:login")


class ResendActivationView(View):
    """Повторная отправка письма активации. POST-only."""

    def post(self, request):
        email = request.POST.get("email", "").strip()
        user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_active:
            send_activation_email(request, user)
        # Всегда одинаковое сообщение — чтобы нельзя было понять,
        # существует ли такой email (защита от user enumeration).
        messages.success(
            request,
            "Если аккаунт с таким email существует и не активирован — "
            "мы отправили письмо повторно.",
        )
        return redirect("accounts:login")


class LoginView(DjangoLoginView):
    """Вход."""
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"С возвращением, {self.request.user.username}!")
        return response

    def form_invalid(self, form):
        # Не дублируем сообщение: если в форме уже есть inactive error,
        # не нужно показывать ещё и "неверный пароль".
        if any(err.code == "inactive" for err in form.non_field_errors().as_data()):
            pass  # сообщение уже в форме
        else:
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
        qs = (
            Recipe.objects
            .filter(author=target_user)
            .annotate(
                avg_rating=Avg("ratings__value"),
                count_ratings=Count("ratings")
            )
            .select_related("category")
        )
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