from django.db.models import F, Q
from django.views.generic import DetailView, ListView

from .models import Recipe, Category


class RecipeListView(ListView):
    """Главная страница: список опубликованных рецептов."""

    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Recipe.objects
            .filter(is_published=True)
            .select_related("author", "category")
        )

        # 1. Фильтрация по категории (если в URL есть ?category=slug)
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # 2. Поиск по тексту (если в URL есть ?q=текст)
        query = self.request.GET.get("q")
        if query:
            # Ищем по названию, описанию и ингредиентам.
            # icontains — регистронезависимый поиск (не важно, большие или маленькие буквы).
            # Q(...) | Q(...) — это логическое "ИЛИ".
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(ingredients__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем все категории в шаблон для отрисовки кнопок фильтра
        context["categories"] = Category.objects.all()
        # Чтобы подсветить активную категорию в меню
        context["current_category"] = self.request.GET.get("category", "")
        # Чтобы сохранить текст поиска в поле ввода
        context["search_query"] = self.request.GET.get("q", "")
        return context

class RecipeDetailView(DetailView):
    """Детальная страница рецепта."""

    model = Recipe
    template_name = "recipes/recipe_detail.html"
    context_object_name = "recipe"
    slug_url_kwarg = "slug"  # ищем по слагу, а не по pk

    def get_queryset(self):
        # select_related — чтобы не делать N+1 при запросе автора и категории
        return Recipe.objects.select_related("author", "category")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Счётчик просмотров: атомарный инкремент через F()
        # Это UPDATE ... SET views_count = views_count + 1, безопасно при параллельных запросах.
        Recipe.objects.filter(pk=obj.pk).update(views_count=F("views_count") + 1)

        # Обновляем объект в памяти, чтобы в шаблоне сразу отобразилось новое число
        obj.refresh_from_db()
        return obj