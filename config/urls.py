from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('recipes.urls')),
]

# В DEBUG=True Django сам отдаёт файлы из MEDIA_ROOT по URL-префиксу MEDIA_URL.
# На продакшене это делает Nginx/S3, поэтому блок обёрнут в if DEBUG.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)