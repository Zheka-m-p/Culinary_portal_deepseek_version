from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager with email as identifier and auto-generated username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)

        # Auto-generate username from email local-part if not provided
        if not extra_fields.get("username"):
            base = (email.split("@")[0] or "user")[:30]
            username = base
            counter = 1
            while self.model.objects.filter(username=username).exists():
                suffix = str(counter)
                username = f"{base[:30 - len(suffix)]}{suffix}"
                counter += 1
            extra_fields["username"] = username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user: login by email OR username; registration by email."""

    # Переопределяем username из AbstractUser: только латиница, цифры, @/./+/-/_
    # Стандартный UnicodeUsernameValidator пропускает кириллицу — нам это не нужно,
    # иначе будут ники вида "ИванПовар" и URL профиля придётся энкодить.
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Только латиница, цифры и @/./+/-/_. Например: chef_ivan."),
        validators=[ASCIIUsernameValidator()],
        error_messages={"unique": _("Пользователь с таким именем уже существует.")},
    )

    email = models.EmailField(_("email address"), unique=True)

    # Аватар. upload_to="avatars/%Y/%m/" — раскладка по папкам, как у рецептов.
    # blank=True — необязательное. null=True НЕ ставим: пустая строка "" — это норма для ImageField.
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/%Y/%m/",
        blank=True,
        help_text=_("Необязательно. JPG/PNG, до 5 МБ."),
    )

    # "О себе" — пара предложений.
    bio = models.TextField(
        _("bio"),
        max_length=500,
        blank=True,
        help_text=_("Необязательно. Расскажите о своих кулинарных предпочтениях."),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # username is auto-generated

    objects = UserManager()

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        from django.urls import reverse
        # Возвращает URL публичного профиля (например: /accounts/profile/username/)
        return reverse("accounts:profile_detail", kwargs={"username": self.username})

    def delete(self, *args, **kwargs):
        """При удалении юзера — удалить его аватар с диска.

        Иначе файлы в media/avatars/ будут копиться мёртвым грузом.
        super().delete() вызываем В КОНЦЕ, чтобы если удаление из БД упадёт,
        файл не пропал зря.
        """
        avatar = self.avatar
        result = super().delete(*args, **kwargs)
        if avatar:
            avatar.delete(save=False)
        return result