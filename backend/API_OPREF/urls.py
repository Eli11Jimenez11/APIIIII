from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from .views import (
    ContratoViewSet, CotizacionViewSet, ServicioViewSet, NovedadViewSet,
    PasswordResetRequestView, PasswordResetVerifyView, CustomTokenObtainPairView
)
from django.http import HttpResponse
from .create_admin_view import CreateAdminView

def login_welcome(request):
    return HttpResponse("Bienvenido a OPREF. Accede con tus credenciales.")

router = DefaultRouter()
router.register(r'contratos', ContratoViewSet)
router.register(r'cotizaciones', CotizacionViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'novedades', NovedadViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # <- cambio aquí
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('api/password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('api/crear-admin/', CreateAdminView.as_view(), name='crear-admin'),
]
