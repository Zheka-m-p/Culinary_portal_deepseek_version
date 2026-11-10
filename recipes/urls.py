from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.RecipeListView.as_view(), name="recipe_list"),
    path("recipes/create/", views.RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<str:slug>/", views.RecipeDetailView.as_view(), name="recipe_detail"),
    path("recipes/<str:slug>/update/", views.RecipeUpdateView.as_view(), name="recipe_update"),
    path("recipes/<str:slug>/delete/", views.RecipeDeleteView.as_view(), name="recipe_delete"),
    # Новый маршрут для переключения статуса
    path("recipes/<str:slug>/toggle-publish/", views.RecipeTogglePublishView.as_view(), name="recipe_toggle_publish"),
]