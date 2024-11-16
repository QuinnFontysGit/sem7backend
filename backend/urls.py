from django.urls import include, path
from rest_framework import routers
from django.contrib import admin
from rest_framework.authtoken import views as auth_views
from backend.webshop.views import register_user, get_csrf_token

from backend.webshop import views

router = routers.DefaultRouter()
router.register(r'carts', views.CartViewSet)
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('csrf/', get_csrf_token, name='get_csrf_token'),
    path('register/', register_user, name='register'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', auth_views.obtain_auth_token, name='api_token_auth'),
]
