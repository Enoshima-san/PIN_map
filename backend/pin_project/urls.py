from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# JWT-эндпоинты (задача #7)
from rest_framework_simplejwt.views import (
     TokenObtainPairView,
     TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    #  JWT-аутентификация
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # получить access+refresh токены
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # обновить access-токен

    #  Остальные API проекта
    path('api/', include('mapapp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
