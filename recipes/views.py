from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CommentForm, RecipeForm
from .models import Category, Comment, Rating, Recipe


def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


class AjaxLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        if is_ajax(self.request):
            return JsonResponse({"ok": False, "error": "login_required"}, status=401)
        return super().handle_no_permission()


class RecipeListView(ListView):
    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Recipe.objects
            .filter(is_published=True)
            .annotate(
                avg_rating=Avg("ratings__value"),
                count_ratings=Count("ratings")
            )
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
        # Аннотируем рейтинг в похожих рецептах — чтобы звёзды работали в карточках
        context["similar_recipes"] = (
            Recipe.objects
            .filter(category=self.object.category, is_published=True)
            .exclude(pk=self.object.pk)
            .annotate(
                avg_rating=Avg("ratings__value"),
                count_ratings=Count("ratings")
            )
            .select_related("author", "category")[:3]
        )

        context["comments"] = (
            self.object.comments
            .select_related("author")
            .order_by("created_at")
        )
        context["comment_form"] = CommentForm()

        user_rating = 0
        if self.request.user.is_authenticated:
            rating_obj = self.object.ratings.filter(user=self.request.user).first()
            if rating_obj:
                user_rating = rating_obj.value
        context["user_rating"] = user_rating

        return context


class RecipeTogglePublishView(LoginRequiredMixin, View):
    def post(self, request, slug):
        recipe = get_object_or_404(Recipe, slug=slug)
        if request.user != recipe.author:
            messages.error(request, "Вы не можете менять статус чужого рецепта.")
            return redirect(recipe.get_absolute_url())
        recipe.is_published = not recipe.is_published
        recipe.save()
        if recipe.is_published:
            messages.success(request, f"Рецепт «{recipe.title}» опубликован!")
        else:
            messages.info(request, f"Рецепт «{recipe.title}» убран в черновики.")
        return redirect(recipe.get_absolute_url())


class RecipeCreateView(LoginRequiredMixin, CreateView):
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


def _render_comment_card(request, comment):
    return render_to_string(
        "recipes/includes/comment_card.html",
        {"comment": comment, "recipe": comment.recipe, "user": request.user},
        request=request,
    )


class CommentCreateView(AjaxLoginRequiredMixin, View):
    def post(self, request, slug):
        recipe = get_object_or_404(Recipe, slug=slug)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.recipe = recipe
            comment.save()
            if is_ajax(request):
                return JsonResponse({"ok": True, "html": _render_comment_card(request, comment)})
            messages.success(request, "Комментарий добавлен.")
            return redirect(recipe.get_absolute_url() + f"#comment-{comment.pk}")
        if is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, "Не удалось добавить комментарий.")
        return redirect(recipe.get_absolute_url() + "#comments")


class CommentUpdateView(AjaxLoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if request.user != comment.author:
            if is_ajax(request):
                return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
            messages.error(request, "Вы не можете редактировать чужой комментарий.")
            return redirect(comment.recipe.get_absolute_url() + f"#comment-{comment.pk}")
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            if is_ajax(request):
                return JsonResponse({"ok": True, "html": _render_comment_card(request, comment)})
            messages.success(request, "Комментарий обновлён.")
            return redirect(comment.recipe.get_absolute_url() + f"#comment-{comment.pk}")
        if is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, "Не удалось обновить комментарий.")
        return redirect(comment.recipe.get_absolute_url() + "#comments")


class CommentDeleteView(AjaxLoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        can_delete = request.user == comment.author or request.user == comment.recipe.author
        if not can_delete:
            if is_ajax(request):
                return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
            messages.error(request, "Вы не можете удалить этот комментарий.")
            return redirect(comment.recipe.get_absolute_url() + f"#comment-{comment.pk}")
        recipe_url = comment.recipe.get_absolute_url()
        comment.delete()
        if is_ajax(request):
            return JsonResponse({"ok": True})
        messages.success(request, "Комментарий удалён.")
        return redirect(recipe_url + "#comments")


class RatingCreateOrUpdateView(AjaxLoginRequiredMixin, View):
    def post(self, request, slug):
        recipe = get_object_or_404(Recipe, slug=slug)
        try:
            value = int(request.POST.get("value", 0))
        except (TypeError, ValueError):
            value = 0
        if not 1 <= value <= 5:
            return JsonResponse({"ok": False, "error": "invalid_value"}, status=400)
        Rating.objects.update_or_create(
            recipe=recipe,
            user=request.user,
            defaults={"value": value},
        )
        return JsonResponse({
            "ok": True,
            "avg": recipe.rating_avg,
            "count": recipe.rating_count,
            "user_value": value,
        })