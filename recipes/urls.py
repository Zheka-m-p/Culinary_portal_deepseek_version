from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    # GET /recipes/ → список рецептов
    path("", views.RecipeListView.as_view(), name="recipe_list"),

    # GET /recipes/create/ → форма создания
    # ВАЖНО: должно идти ДО <str:slug>/, иначе "create" будет пойман как слаг
    path("create/", views.RecipeCreateView.as_view(), name="recipe_create"),

    # GET /recipes/<slug>/ → детальная
    path("<str:slug>/", views.RecipeDetailView.as_view(), name="recipe_detail"),

    # GET /recipes/<slug>/update/ → форма редактирования
    path("<str:slug>/update/", views.RecipeUpdateView.as_view(), name="recipe_update"),

    # GET /recipes/<slug>/delete/ → подтверждение удаления
    path("<str:slug>/delete/", views.RecipeDeleteView.as_view(), name="recipe_delete"),

    # POST /recipes/<slug>/toggle-publish/ → переключение статуса
    path("<str:slug>/toggle-publish/", views.RecipeTogglePublishView.as_view(), name="recipe_toggle_publish"),

    # POST /recipes/<slug>/comment/add/ → добавление комментария
    path("<str:slug>/comment/add/", views.CommentCreateView.as_view(), name="comment_create"),

    # POST /comments/<pk>/update/ → редактирование комментария
    path("comments/<int:pk>/update/", views.CommentUpdateView.as_view(), name="comment_update"),

    # POST /comments/<pk>/delete/ → удаление комментария
    path("comments/<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),

    # POST /recipes/<slug>/rate/ → поставить/изменить оценку
    path("<str:slug>/rate/", views.RatingCreateOrUpdateView.as_view(), name="recipe_rating"),
]