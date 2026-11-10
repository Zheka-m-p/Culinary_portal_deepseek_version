from django import forms
from .models import Recipe, Comment


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


class CommentForm(forms.ModelForm):
    """Форма для добавления и редактирования комментария.

    Поля author и recipe сюда НЕ включены намеренно.
    Их мы будем брать из request.user и URL во вьюхе.
    Если добавить их сюда, хакер сможет через curl подделать автора.
    """

    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Напишите комментарий...",
            }),
        }
        labels = {
            "text": "",  # Убираем стандартный лейбл, используем placeholder
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Накидываем Bootstrap-класс
        self.fields["text"].widget.attrs.update({"class": "form-control"})

        # Убираем атрибут required у HTML-тега, чтобы валидацией занимался Django (и выдавал красивые ошибки).
        # Для AJAX это не критично, но для fallback (без JS) — полезно.
        self.fields["text"].widget.attrs.pop("required", None)