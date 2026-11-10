# 🍳 Кулинарный портал

Веб-приложение для публикации кулинарных рецептов с возможностью комментирования. Написан на Django 5.2 как учебный проект уровня production-подхода: кастомный пользователь, безопасность, AJAX-взаимодействие без перезагрузки.

## ✨ Функционал

### Рецепты
- 📝 Публикация рецептов с заголовком, категорией, описанием, ингредиентами, шагами, изображением, временем готовки и количеством порций.
- 🖼️ Загрузка фотографий рецептов (`media/recipes/`).
- 👤 CRUD только для автора — нельзя редактировать/удалять чужие рецепты.
- 📤 Черновики и публикация: рецепт не виден другим, пока не опубликован.
- ⚡ Быстрое переключение статуса «Опубликован ↔ Черновик» прямо со страницы рецепта.
- 📊 Счётчик просмотров с атомарным инкрементом через `F()` (без гонок).

### Категории и поиск
- 🗂️ Фильтрация по категориям (Супы, Десерты, Вторые блюда, Салаты).
- 🔍 Поиск по заголовку, описанию и ингредиентам.
- 📄 Пагинация (12 рецептов на страницу).
- 🔄 Похожие рецепты (из той же категории).

### Пользователи
- 🔐 Кастомная модель `User` с логином по **email ИЛИ username**.
- ✉️ Регистрация по email.
- 👤 Профиль с аватаром, био, табами «Все / Опубликованные / Черновики».
- 🔒 Приватность: email, черновики и полная статистика видны только владельцу.
- ✏️ Редактирование профиля: логин, email, ФИО, аватар, био.

### Комментарии
- 💬 Добавление, редактирование и удаление комментариев **без перезагрузки страницы** (AJAX + `fetch`).
- 🎯 Инлайн-редактирование (без модальных окон).
- 🛡️ Права: свой комментарий — правь и удаляй; под своим рецептом — можешь удалять чужие (модерация).
- 🎨 Прогрессивное улучшение: без JS всё работает через обычный POST (fallback).

## 🛠️ Стек

| Компонент | Версия |
|---|---|
| Python | 3.14+ |
| Django | 5.2 LTS |
| База данных | SQLite |
| python-decouple | 3.8 (переменные окружения) |
| Pillow | Загрузка изображений |
| Bootstrap | 5.3 (CDN) |
| Bootstrap Icons | 1.11 (CDN) |

## 🚀 Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Zheka-m-p/Culinary_portal_deepseek_version.git
cd Culinary_portal_deepseek_version

# 2. Создать виртуальное окружение
python -m venv .venv

# 3. Активировать (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# (Linux/macOS: source .venv/bin/activate)

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Создать .env на основе шаблона
copy .env.example .env
# (Linux/macOS: cp .env.example .env)

# 6. Сгенерировать SECRET_KEY и вставить в .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 7. Применить миграции
python manage.py migrate

# 8. Создать суперпользователя
python manage.py createsuperuser

# 9. Запустить dev-сервер
python manage.py runserver
```

После запуска откройте в браузере: `http://127.0.0.1:8000`

## 🔧 Переменные окружения (`.env`)

```dotenv
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Все секреты хранятся в `.env`, который не коммитится в репозиторий. Шаблон находится в `.env.example`.

## 📁 Структура проекта

```text
.
├── config/                  # настройки Django
│   ├── settings.py
│   └── urls.py
├── accounts/                # пользователи, аутентификация, профили
│   ├── models.py            # кастомный User (AbstractUser + email + avatar + bio)
│   ├── backends.py          # EmailOrUsernameBackend
│   ├── forms.py
│   ├── views.py
│   └── admin.py
├── recipes/                 # рецепты, категории, комментарии
│   ├── models.py            # Category, Recipe, Comment
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/recipes/
├── templates/               # общие шаблоны
│   ├── base.html
│   └── includes/
│       ├── navbar.html
│       └── footer.html
├── media/                   # пользовательские загрузки (не в git)
│   ├── recipes/
│   └── avatars/
├── staticfiles/             # собранная статика для продакшена (не в git)
├── .env                     # секреты (не в git)
├── .env.example             # шаблон
├── .gitignore
├── manage.py
└── requirements.txt
```

## 🔒 Безопасность

- ✅ `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` вынесены в `.env`.
- ✅ `.env`, `db.sqlite3`, `media/`, `staticfiles/`, `.venv/`, `__pycache__/` добавлены в `.gitignore`.
- ✅ Кастомная модель `User` создана до первых миграций.
- ✅ CSRF-защита во всех формах, включая AJAX (через `X-CSRFToken`).
- ✅ Logout работает только через POST (защита от CSRF-атак через GET).
- ✅ Проверка прав на сервере (`UserPassesTestMixin`, явные проверки во вьюхах) — не только в шаблонах.
- ✅ Защита от open-redirect при `?next=` (`url_has_allowed_host_and_scheme`).
- ✅ Использование `format_html` в админке (защита от XSS).

## 🧪 Проверка работоспособности

```bash
python manage.py check
```

Команда должна вывести: `System check identified no issues (0 silenced).`

## 🗺️ Что дальше (TODO)

- [ ] Кастомные страницы 404 и 500.
- [ ] Смена пароля через `PasswordChangeView`.
- [ ] Восстановление пароля по email (Яндекс SMTP).
- [ ] Подтверждение email при регистрации.
- [ ] Комментарии с вложенностью (ответы на комментарии).
- [ ] Рейтинги / лайки рецептов.
- [ ] Категории в навбаре (dropdown).
- [ ] Свой дизайн вместо стандартного Bootstrap.

## 📄 Лицензия

Учебный проект. Свободен для использования в образовательных целях.

**Автор:** [Zheka-m-p](https://github.com/Zheka-m-p)