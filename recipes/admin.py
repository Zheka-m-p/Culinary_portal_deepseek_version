from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Comment, Recipe


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "recipes_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        # Аннотируем количество рецептов ОДНИМ запросом, а не по строке в списке.
        # Без annotate получилось бы N+1: отдельный COUNT для каждой категории.
        return super().get_queryset(request).annotate(recipes_total=Count("recipes"))

    @admin.display(description=_("рецептов"), ordering="recipes_total")
    def recipes_count(self, obj):
        return obj.recipes_total


class CommentInline(admin.TabularInline):
    """Комментарии прямо на странице редактирования рецепта."""

    model = Comment
    extra = 0                          # не показывать пустые формы «добавить»
    fields = ("author", "text", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)        # новые сверху
    autocomplete_fields = ("author",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "title", "author", "category", "is_published",
        "views_count", "created_at", "thumbnail", 
    )
    list_filter = ("is_published", "category", "created_at")
    search_fields = ("title", "description", "ingredients",
                     "author__email", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views_count", "created_at", "updated_at", "preview_image")
    autocomplete_fields = ("author", "category")
    list_editable = ("is_published",)
    date_hierarchy = "created_at"
    inlines = [CommentInline]

    fieldsets = (
        (_("Основное"), {
            "fields": ("title", "slug", "author", "category", "is_published"),
        }),
        (_("Содержание"), {
            "fields": ("description", "ingredients", "steps"),
        }),
        (_("Параметры"), {
            "fields": ("cooking_time", "servings"),
        }),
        (_("Изображение"), {
            "fields": ("image", "preview_image"),
        }),
        (_("Служебное"), {
            "fields": ("views_count", "created_at", "updated_at"),
        }),
    )

    @admin.display(description=_("превью"))
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />',
                obj.image.url,
            )
        return "—"

    @admin.display(description=_("предпросмотр"))
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:300px;border-radius:6px;" />',
                obj.image.url,
            )
        return "—"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_text", "author", "recipe", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("text", "author__email", "author__username", "recipe__title")
    autocomplete_fields = ("author", "recipe")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description=_("текст"))
    def short_text(self, obj):
        return obj.text[:60] + ("..." if len(obj.text) > 60 else "")