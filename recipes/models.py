from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Категория рецептов: Супы, Салаты, Десерты и т.д."""

    name = models.CharField(_("название"), max_length=100, unique=True)
    slug = models.SlugField(_("слаг"), max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _("категория")
        verbose_name_plural = _("категории")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Слаг генерим автоматически из названия, если не задан вручную.
        # allow_unicode=True — чтобы кириллица ("Супы" → "супы") не вырезалась.
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Recipe(models.Model):
    """Рецепт: заголовок, автор, категория, ингредиенты, шаги, фото и т.д."""

    title = models.CharField(_("заголовок"), max_length=200)
    slug = models.SlugField(_("слаг"), max_length=200, unique=True, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,        # удалили юзера → удалились его рецепты
        related_name="recipes",          # user.recipes.all()
        verbose_name=_("автор"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,        # нельзя удалить категорию, пока в ней есть рецепты
        related_name="recipes",          # category.recipes.all()
        verbose_name=_("категория"),
    )

    description = models.TextField(_("краткое описание"), blank=True)
    ingredients = models.TextField(_("ингредиенты"))
    steps = models.TextField(_("шаги приготовления"))

    # upload_to с %Y/%m/ — файлы раскладываются по папкам "2026/11/",
    # иначе в одной папке со временем будет каша из тысяч файлов.
    image = models.ImageField(
        _("изображение"), upload_to="recipes/%Y/%m/", blank=True
    )

    cooking_time = models.PositiveIntegerField(
        _("время приготовления (мин)"),
        validators=[MinValueValidator(1)],
    )
    servings = models.PositiveSmallIntegerField(
        _("количество порций"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
    )

    # is_published=True — рецепт виден всем. По умолчанию черновик.
    is_published = models.BooleanField(_("опубликован"), default=False)

    # editable=False — нельзя менять из форм и админки.
    # Счётчик обновляем только через F() в коде, иначе гонки при параллельных запросах.
    views_count = models.PositiveIntegerField(
        _("просмотры"), default=0, editable=False
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("рецепт")
        verbose_name_plural = _("рецепты")
        ordering = ("-created_at",)      # новые сверху
        indexes = [
            # «последние N рецептов»
            models.Index(fields=["-created_at"]),
            # самый частый запрос: опубликованные, новые сверху (главная)
            models.Index(fields=["is_published", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Автогенерация слага из заголовка с дедупом (-1, -2, ...).
        if not self.slug:
            base = slugify(self.title, allow_unicode=True)[:180] or "recipe"
            slug = base
            counter = 1
            # exclude(pk=self.pk) — чтобы при редактировании рецепт не «нашёл сам себя»
            while Recipe.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{counter}"
                slug = f"{base[:180 - len(suffix)]}{suffix}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Используется в админке (кнопка «Посмотреть на сайте»),
        # в шаблонах {{ recipe.get_absolute_url }} и в redirect(recipe).
        return reverse("recipes:recipe_detail", kwargs={"slug": self.slug})


class Comment(models.Model):
    """Комментарий к рецепту."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,        # удалили рецепт → удалились его комменты
        related_name="comments",         # recipe.comments.all()
        verbose_name=_("рецепт"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,        # удалили юзера → удалились его комменты
        related_name="comments",         # user.comments.all()
        verbose_name=_("автор"),
    )

    text = models.TextField(_("текст"), max_length=2000)

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("комментарий")
        verbose_name_plural = _("комментарии")
        ordering = ("created_at",)       # старые сверху, как в форумах

    def __str__(self):
        # Обрезаем текст, чтобы в админке и в консоли было читаемо.
        return f"{self.author} → {self.recipe}: {self.text[:30]}"