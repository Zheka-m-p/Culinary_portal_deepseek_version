from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RecipeForm
from .models import Category, Recipe


class RecipeListView(ListView):
    """Главная: только опубликованные рецепты."""
    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 12

    def get_queryset(self):
        # Строгий фильтр: только опубликованные.
        queryset = (
            Recipe.objects
            .filter(is_published=True)
            .select_related("author", "category")
        )

        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(ingredients__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class RecipeDetailView(DetailView):
    """Детальная страница. Черновики видны только автору."""
    model = Recipe
    template_name = "recipes/recipe_detail.html"
    context_object_name = "recipe"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = Recipe.objects.select_related("author", "category")
        if self.request.user.is_authenticated:
            return qs.filter(Q(is_published=True) | Q(author=self.request.user))
        return qs.filter(is_published=True)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_published:
            Recipe.objects.filter(pk=obj.pk).update(views_count=F("views_count") + 1)
            obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["similar_recipes"] = Recipe.objects.filter(
            category=self.object.category,
            is_published=True,
        ).exclude(pk=self.object.pk).select_related("author", "category")[:3]
        return context


class RecipeTogglePublishView(LoginRequiredMixin, View):
    """Быстрое переключение статуса: Опубликован <-> Черновик."""

    def post(self, request, slug):
        recipe = get_object_or_404(Recipe, slug=slug)

        # Проверка прав: только автор может менять статус
        if request.user != recipe.author:
            messages.error(request, "Вы не можете менять статус чужого рецепта.")
            return redirect(recipe.get_absolute_url())

        # Переключаем статус
        recipe.is_published = not recipe.is_published
        recipe.save()

        if recipe.is_published:
            messages.success(request, f"Рецепт «{recipe.title}» опубликован!")
        else:
            messages.info(request, f"Рецепт «{recipe.title}» убран в черновики.")

        return redirect(recipe.get_absolute_url())


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """Создание рецепта."""
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        if self.object.is_published:
            messages.success(self.request, f"Рецепт «{self.object.title}» опубликован!")
        else:
            messages.info(self.request, f"Рецепт «{self.object.title}» сохранён как черновик.")
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование рецепта."""
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"
    raise_exception = True

    def test_func(self):
        return self.request.user == self.get_object().author

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Рецепт «{self.object.title}» обновлён.")
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class RecipeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление рецепта."""
    model = Recipe
    template_name = "recipes/recipe_confirm_delete.html"
    success_url = reverse_lazy("recipes:recipe_list")
    raise_exception = True

    def test_func(self):
        return self.request.user == self.get_object().author

    def form_valid(self, form):
        title = self.object.title
        response = super().form_valid(form)
        messages.warning(self.request, f"Рецепт «{title}» удалён.")
        return response