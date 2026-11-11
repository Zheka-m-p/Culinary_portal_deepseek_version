from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
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
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Recipe(models.Model):
    """Рецепт: заголовок, автор, категория, ингредиенты, шаги, фото и т.д."""
    title = models.CharField(_("заголовок"), max_length=200)
    slug = models.SlugField(_("слаг"), max_length=200, unique=True, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name=_("автор"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="recipes",
        verbose_name=_("категория"),
    )

    description = models.TextField(_("краткое описание"), blank=True)
    ingredients = models.TextField(_("ингредиенты"))
    steps = models.TextField(_("шаги приготовления"))

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

    is_published = models.BooleanField(_("опубликован"), default=False)
    views_count = models.PositiveIntegerField(
        _("просмотры"), default=0, editable=False
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("рецепт")
        verbose_name_plural = _("рецепты")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_published", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True)[:180] or "recipe"
            slug = base
            counter = 1
            while Recipe.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{counter}"
                slug = f"{base[:180 - len(suffix)]}{suffix}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("recipes:recipe_detail", kwargs={"slug": self.slug})

    # --- Свойства для рейтинга (удобно вызывать из шаблона) ---
    @property
    def rating_avg(self):
        """Средний рейтинг (0, если оценок нет). Округляем до 1 знака."""
        result = self.ratings.aggregate(avg=Avg("value"))["avg"]
        return round(result, 1) if result else 0

    @property
    def rating_count(self):
        """Количество оценок."""
        return self.ratings.count()


class Comment(models.Model):
    """Комментарий к рецепту."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("рецепт"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("автор"),
    )

    text = models.TextField(_("текст"), max_length=2000)

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("комментарий")
        verbose_name_plural = _("комментарии")
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.author} → {self.recipe}: {self.text[:30]}"


class Rating(models.Model):
    """Оценка рецепта пользователем (1-5 звёзд)."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("рецепт"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("пользователь"),
    )
    value = models.PositiveSmallIntegerField(
        _("оценка"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("оценка")
        verbose_name_plural = _("оценки")
        # Один юзер — одна оценка на один рецепт
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_recipe_user_rating",
            )
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} → {self.recipe}: {self.value}/5"