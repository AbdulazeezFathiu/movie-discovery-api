
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Existing API routes
    path('api/', include('movies.urls')),
    path('api/auth/', include('accounts.urls')),

    # OpenAPI schema
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),

    # Swagger documentation
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema'
        ),
        name='swagger-ui'
    ),

    # ReDoc documentation
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(
            url_name='schema'
        ),
        name='redoc'
    ),
]
