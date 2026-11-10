from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("recipes/", include("recipes.urls")),

    # Редирект с корня на список рецептов, чтобы "/" не давал 404.
    # permanent=False — временный (302), а не постоянный (301),
    # чтобы браузеры не кэшировали редирект. На проде можно поменять на True.
    path("", RedirectView.as_view(pattern_name="recipes:recipe_list", permanent=False)),
]

# В DEBUG=True Django сам отдаёт файлы из MEDIA_ROOT по URL-префиксу MEDIA_URL.
# На продакшене это делает Nginx/S3, поэтому блок обёрнут в if DEBUG.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)