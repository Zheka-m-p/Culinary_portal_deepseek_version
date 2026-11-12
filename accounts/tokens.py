"""Генерация и проверка токенов подтверждения email.

Используем django.core.signing.TimestampSigner — это встроенный механизм Django,
который подписывает данные SECRET_KEY'ом и добавляет метку времени.

Альтернативы:
- Модель EmailConfirmation с UUID в БД — надёжнее (можно отозвать конкретный токен),
  но требует таблицу, миграцию и логику очистки. Оверкилл для нашего случая.
- secrets.token_urlsafe() + хранение в БД — то же самое, только руками.
- JWT — оверкилл, тянет зависимость.

TimestampSigner даёт нам "бесплатно":
1. Подпись — токен нельзя подделать без SECRET_KEY.
2. Срок жизни — max_age проверяется при валидации.
3. Привязку к user.pk — токен "привязан" к конкретному юзеру.

Минус: нельзя "отозвать" один токен (только сменив SECRET_KEY или дождавшись истечения).
Для email-подтверждения это не проблема — токен живёт 3 дня, юзер либо активируется, либо нет.
"""

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

# Salt — чтобы токены активации нельзя было спутать с другими токенами
# (например, если завтра мы добавим "токен сброса пароля", у него будет свой salt).
SALT = "email-activation"

# Сколько живёт токен: 3 дня. Хватает, если юзер зарегистрировался в пятницу вечером
# и вспомнил про письмо в понедельник.
MAX_AGE_SECONDS = 3 * 24 * 60 * 60

signer = TimestampSigner(salt=SALT)


def generate_token(user) -> str:
    """Создаёт подписанный токен для активации аккаунта юзера.

    Возвращает строку вида: '42:1a2b3c4d...' — внутри подпись и timestamp.
    """
    return signer.sign(str(user.pk))


def verify_token(token: str):
    """Проверяет токен. Возвращает pk юзера или None, если токен невалиден/истёк."""
    try:
        pk_str = signer.unsign(token, max_age=MAX_AGE_SECONDS)
        return int(pk_str)
    except (BadSignature, SignatureExpired, ValueError):
        # BadSignature — токен подделан или испорчен (например, обрезан в URL).
        # SignatureExpired — токен старше MAX_AGE_SECONDS.
        # ValueError — внутри токена не число (не должно случаться, но страховка).
        return None