from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomAuthTokenSerializer
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.utils.crypto import get_random_string
from .models import Contrato, Cotizacion, Servicio, Novedad, PasswordResetCode, User
from .serializers import (
    ContratoSerializer,
    CotizacionSerializer,
    ServicioSerializer,
    NovedadSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer
)
from django.contrib.auth import get_user_model
from django.core.management import call_command
import os

User = get_user_model()


def home(request):
    try:
        send_mail(
            subject='Prueba SMTP desde Render',
            message='Este es un email de prueba',
            from_email=settings.EMAIL_HOST_USER,  # Solo email
            recipient_list=['eli11jimenez11@gmail.com'],  # Cambia esto
            fail_silently=False
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # No reveles que el email no existe por seguridad
            return Response(
                {'message': 'Si este email existe en nuestro sistema, recibirás un código de recuperación'},
                status=status.HTTP_200_OK
            )

        # Generar código
        code = get_random_string(length=6, allowed_chars='0123456789')
        
        # Eliminar códigos previos
        PasswordResetCode.objects.filter(email=email).delete()
        
        # Crear nuevo código
        reset_code = PasswordResetCode.objects.create(
            email=email,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Enviar email
        try:
            send_mail(
                'Código de recuperación - OPREF',
                f'Tu código de recuperación es: {code}\n\nVálido por 10 minutos.',
                settings.EMAIL_HOST_USER,  # Usa el email directamente
                [email],
                fail_silently=False
            )
            return Response(
                {'message': 'Si este email existe en nuestro sistema, recibirás un código de recuperación'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            return Response(
                {'error': 'Error al enviar el correo. Por favor intenta más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PasswordResetVerifyView(APIView):
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data.get('new_password')
        verify_only = request.data.get('verify_only', False)

        # Buscar usuario y código
        user = User.objects.filter(email=email).first()
        reset_code = PasswordResetCode.objects.filter(
            email=email,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()

        if not user or not reset_code:
            return Response(
                {"detail": "Código incorrecto o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verify_only:
            return Response(
                {"detail": "Código válido"},
                status=status.HTTP_200_OK
            )

        # Cambiar contraseña
        user.set_password(new_password)
        user.save()
        
        # Marcar código como usado
        reset_code.is_used = True
        reset_code.save()

        return Response(
            {"detail": "Contraseña actualizada correctamente"},
            status=status.HTTP_200_OK
        )
    
    
class CustomTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MigrateView(APIView):
    def get(self, request):
        try:
            call_command('migrate')
            return JsonResponse({'message': 'Migraciones aplicadas correctamente.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
def env_check(request):
    env_vars = {
        'EMAIL_HOST_USER_EXISTS': 'EMAIL_HOST_USER' in os.environ,
        'EMAIL_HOST_PASSWORD_EXISTS': 'EMAIL_HOST_PASSWORD' in os.environ,
        'IS_RENDER': 'RENDER' in os.environ,
        'SMTP_CONFIGURED': all(
            key in os.environ 
            for key in ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']
        )
    }
    return JsonResponse(env_vars)