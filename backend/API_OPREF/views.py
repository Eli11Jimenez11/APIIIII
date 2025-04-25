import os
import logging
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Contrato, Cotizacion, Servicio, Novedad, PasswordResetCode
from .serializers import (
    ContratoSerializer,
    CotizacionSerializer,
    ServicioSerializer,
    NovedadSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    CustomAuthTokenSerializer
)

# Configurar logger para capturar errores
logger = logging.getLogger(__name__)
User = get_user_model()


def home(request):
    print("Home view accessed")
    return JsonResponse({'message': 'Bienvenido a la API de OPREF'})


# CRUD Views para modelos básicos
class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer


class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = Cotizacion.objects.all()
    serializer_class = CotizacionSerializer


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer


class NovedadViewSet(viewsets.ModelViewSet):
    queryset = Novedad.objects.all()
    serializer_class = NovedadSerializer


class PasswordResetRequestView(APIView):
    permission_classes = []  # acceso público

    def post(self, request):
        try:
            serializer = PasswordResetRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']

            # Generar y almacenar el código
            code = get_random_string(length=6, allowed_chars='0123456789')
            PasswordResetCode.objects.filter(email=email).delete()
            PasswordResetCode.objects.create(
                email=email,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            return Response(
                {'message': 'Código generado correctamente', 'code': code},
                status=status.HTTP_200_OK
            )
        except Exception:
            logger.error("Error en PasswordResetRequestView", exc_info=True)
            return Response(
                {'detail': 'Error interno al generar el código, inténtalo más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetCodeValidationView(APIView):
    """
    Verifica que el código exista, no esté usado y no haya expirado.
    """
    permission_classes = []  # Sin permisos, acceso público

    def post(self, request):
        try:
            # Valida los datos de entrada (email y código)
            serializer = PasswordResetVerifySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)  # Validación de los datos
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            # Verifica si el código existe y es válido
            exists = PasswordResetCode.objects.filter(
                email=email,
                code=code,
                is_used=False,  # Verifica que no haya sido usado
                expires_at__gt=timezone.now()  # Verifica que no haya expirado
            ).exists()

            if not exists:
                # Si no existe o no es válido, retorna un error 400
                return Response({'detail': 'Código incorrecto o expirado'}, status=status.HTTP_400_BAD_REQUEST)

            # Si el código es válido, retorna una respuesta de éxito
            return Response({'detail': 'Código válido'}, status=status.HTTP_200_OK)
        except Exception:
            # Manejo de excepciones en caso de error
            logger.error("Error en PasswordResetCodeValidationView", exc_info=True)
            return Response(
                {'detail': 'Error interno al validar el código.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PasswordResetConfirmView(APIView):
    """
    Confirma y aplica el cambio de contraseña.
    Requiere 'email', 'code' y 'new_password'.
    """
    permission_classes = []  # Sin permisos, acceso público

    def post(self, request):
        try:
            # Deserializar los datos de entrada
            serializer = PasswordResetVerifySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = request.data.get('new_password')  # Obtener la nueva contraseña desde el cuerpo de la solicitud

            # Validar que la nueva contraseña esté presente
            if not new_password:
                return Response({'detail': 'Nueva contraseña requerida.'}, status=status.HTTP_400_BAD_REQUEST)

            # Buscar el código de recuperación
            reset_code = PasswordResetCode.objects.filter(
                email=email,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()  # Verificar si el código ha expirado
            ).first()

            if not reset_code:
                return Response({'detail': 'Código incorrecto o expirado'}, status=status.HTTP_400_BAD_REQUEST)

            # Buscar al usuario por email
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            # Cambiar la contraseña del usuario
            user.set_password(new_password)
            user.save()

            # Marcar el código como usado
            reset_code.is_used = True
            reset_code.save()

            return Response({'detail': 'Contraseña actualizada correctamente'}, status=status.HTTP_200_OK)
        except Exception:
            logger.error("Error en PasswordResetConfirmView", exc_info=True)
            return Response(
                {'detail': 'Error interno al confirmar contraseña.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CustomTokenObtainPairView(APIView):
    """
    Obtener pares de tokens JWT personalizados.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            serializer = CustomAuthTokenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({'access': str(refresh.access_token), 'refresh': str(refresh)}, status=status.HTTP_200_OK)
        except Exception:
            logger.error("Error en CustomTokenObtainPairView", exc_info=True)
            return Response({'detail': 'Error de autenticación.'}, status=status.HTTP_400_BAD_REQUEST)


class MigrateView(APIView):
    """
    Ejecuta migraciones desde la URL (solo para testing).
    """
    permission_classes = []

    def get(self, request):
        try:
            call_command('migrate')
            return JsonResponse({'message': 'Migraciones aplicadas correctamente.'})
        except Exception:
            logger.error("Error en MigrateView", exc_info=True)
            return JsonResponse({'error': 'Error interno al aplicar migraciones.'}, status=500)


def env_check(request):
    """
    Comprueba las variables de entorno relacionadas con SMTP y Render.
    """
    env_vars = {
        'EMAIL_HOST_USER_EXISTS': 'EMAIL_HOST_USER' in os.environ,
        'EMAIL_HOST_PASSWORD_EXISTS': 'EMAIL_HOST_PASSWORD' in os.environ,
        'IS_RENDER': 'RENDER' in os.environ,
        'SMTP_CONFIGURED': all(k in os.environ for k in ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']),
    }
    return JsonResponse(env_vars)


def health_check(request):
    """
    Health check básico.
    """
    return JsonResponse({'status': 'ok'})
