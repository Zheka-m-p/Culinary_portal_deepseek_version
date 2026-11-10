from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    """Форма регистрации."""

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text="На этот адрес можно будет восстановить пароль.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Имя пользователя",
        }
        help_texts = {
            "username": "Буквы, цифры и @/./+/-/_. Например: chef_ivan.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if name in ("password1", "password2"):
                field.widget.attrs.update({"autocomplete": "new-password"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username


class LoginForm(AuthenticationForm):
    """Форма входа."""

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


class ProfileUpdateForm(forms.ModelForm):
    """Форма редактирования профиля.

    Разрешаем менять username, email, имя и фамилию.
    Пароль здесь НЕ меняем — для него будет отдельная форма/вьюха (стандарт Django).
    """

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        labels = {
            "username": "Имя пользователя",
            "email": "Email",
            "first_name": "Имя",
            "last_name": "Фамилия",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Например: Иван"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Например: Иванов"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        """Проверяем уникальность email, ИСКЛЮЧАЯ текущего юзера.

        exclude(pk=self.instance.pk) — важно, иначе при сохранении без изменения email
        Django скажет "такой email уже занят", потому что найдёт самого же юзера в БД.
        """
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот email уже занят другим пользователем.")
        return email

    def clean_username(self):
        """Аналогично — уникальность username, исключая себя же."""
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username