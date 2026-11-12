"""Утилиты для accounts: отправка писем и т.п.

Отдельный файл, потому что отправка письма — это не вьюха и не модель,
это переиспользуемая функция (вызываем и из RegisterView, и из ResendActivationView).
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from .tokens import generate_token


def send_activation_email(request, user):
    """Отправляет письмо со ссылкой активации.

    Почему EmailMultiAlternatives, а не send_mail:
    - send_mail — только plain text. Старые почтовики довольны, но выглядит бедно.
    - EmailMultiAlternatives позволяет добавить HTML-версию через attach_alternative,
      при этом plain-text остаётся в теле (fallback для старых клиентов и для
      спам-фильтров, которые не любят письма "только HTML").
    """
    token = generate_token(user)

    # build_absolute_uri превращает относительный URL в полный:
    # "/accounts/activate/42:abc..." → "http://127.0.0.1:8000/accounts/activate/42:abc..."
    # На проде автоматически станет "https://culinary-portal.ru/accounts/activate/..."
    activation_url = request.build_absolute_uri(
        reverse("accounts:activate", kwargs={"token": token})
    )

    context = {
        "user": user,
        "activation_url": activation_url,
    }

    subject = "Подтвердите email на Кулинарном портале"
    text_body = render_to_string("emails/activation_email.txt", context)
    html_body = render_to_string("emails/activation_email.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,                # plain-text версия
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")  # HTML-версия
    msg.send()