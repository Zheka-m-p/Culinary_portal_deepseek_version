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
            "username": "Логин",
        }
        help_texts = {
            "username": "Только латиница, цифры и @/./+/-/_. Например: chef_ivan.",
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
        label="Email или логин",
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
    """Форма редактирования профиля."""

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "avatar", "bio")
        labels = {
            "username": "Логин",
            "email": "Email",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "avatar": "Аватар",
            "bio": "О себе",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Например: Иван"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Например: Иванов"}),
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Люблю готовить пасту и печь хлеб..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # В Bootstrap 5 для файлов используется тот же класс form-control
            field.widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот email уже занят другим пользователем.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username