from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    ContratoViewSet, CotizacionViewSet, ServicioViewSet, NovedadViewSet,
    PasswordResetRequestView, PasswordResetVerifyView, CustomTokenObtainPairView
)
from django.http import HttpResponse
from .create_admin_view import CreateAdminView
from django.contrib import admin
from .views import home, MigrateView, env_check

def login_welcome(request):
    return HttpResponse("Bienvenido a OPREF. Accede con tus credenciales.")

router = DefaultRouter()
router.register(r'contratos', ContratoViewSet)
router.register(r'cotizaciones', CotizacionViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'novedades', NovedadViewSet)

urlpatterns = [
    path('', home),  # <<< Esto agrega la raíz
    path('admin/', admin.site.urls),
    path('', include(router.urls)),  # Rutas de la API
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'), # La vista personalizada para la página de login
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('crear-admin/', CreateAdminView.as_view(), name='crear-admin'),
    path('migrate/', MigrateView.as_view(), name='migrate'),
    path('env-check/', env_check, name='env_check'),
]