from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    """Форма регистрации.

    Наследуемся от UserCreationForm — там уже реализованы:
    - поля password1 и password2
    - сравнение паролей (clean_password2)
    - валидация пароля через AUTH_PASSWORD_VALIDATORS (длина, сложность и т.д.)
    - save() с правильным хэшированием (set_password)

    Мы добавляем email (у UserCreationForm его нет) и стилизуем поля под Bootstrap.
    """

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text="На этот адрес можно будет восстановить пароль.",
    )

    class Meta:
        model = User
        # username нужен для отображения в профиле, email — для входа и связи.
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Имя пользователя",
        }
        help_texts = {
            "username": "Буквы, цифры и @/./+/-/_. Например: chef_ivan.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Единообразно применяем Bootstrap-классы ко всем полям.
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            # Поля паролей не должны кэшироваться браузером
            if name in ("password1", "password2"):
                field.widget.attrs.update({"autocomplete": "new-password"})

    def clean_email(self):
        """Проверка, что email ещё не занят.

        Хотя в модели у email стоит unique=True, ошибка от БД выглядит страшно
        (IntegrityError). Лучше поймать её здесь и вернуть понятное сообщение.
        Приводим к нижнему регистру для сравнения — чтобы Test@X.com и test@x.com
        считались одним и тем же адресом (мы это уже делали в UserManager).
        """
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean_username(self):
        """Проверка уникальности username (без учёта регистра).

        В модели username unique=True, но это регистрозависимо на уровне БД.
        Хотим, чтобы Ivan и ivan считались дублем — тогда логин по username
        через наш backend (там iexact) не выберет непонятно кого.
        """
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username


class LoginForm(AuthenticationForm):
    """Форма входа.

    Стандартная AuthenticationForm ожидает username + password.
    У нас через кастомный EmailOrUsernameBackend можно вводить и email, и username.
    Поэтому переопределяем только label и help_text, а логику оставляем стандартной.
    """

    username = forms.CharField(
        label="Email или имя пользователя",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

