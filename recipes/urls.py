from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.RecipeListView.as_view(), name="recipe_list"),
    path("recipes/<str:slug>/", views.RecipeDetailView.as_view(), name="recipe_detail"),
]