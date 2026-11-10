from django import forms
from .models import Recipe


class RecipeForm(forms.ModelForm):
    """Форма для создания и редактирования рецепта."""

    class Meta:
        model = Recipe
        # Выбираем поля, которые юзер может заполнять.
        # author, slug и views_count сюда НЕ входят — они заполняются автоматически.
        fields = (
            "title", "category", "description", "ingredients",
            "steps", "image", "cooking_time", "servings", "is_published"
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "ingredients": forms.Textarea(attrs={"rows": 5}),
            "steps": forms.Textarea(attrs={"rows": 7}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Автоматически добавляем Bootstrap-классы ко всем полям,
        # чтобы не прописывать их вручную в шаблоне.
        for field_name, field in self.fields.items():
            if field_name == "is_published":
                # Для чекбокса нужен класс form-check-input
                field.widget.attrs.update({"class": "form-check-input"})
            elif field_name == "category":
                # Для выпадающего списка нужен класс form-select
                field.widget.attrs.update({"class": "form-select"})
            else:
                # Для остальных (текст, числа, файлы) — form-control
                field.widget.attrs.update({"class": "form-control"})