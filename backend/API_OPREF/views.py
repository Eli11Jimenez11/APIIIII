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
)
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

def home(request):
    return JsonResponse({'mensaje': 'API OPREF funcionandoooo correctamente 🚀'})

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
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'Este correo no está registrado.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generar código
            code = get_random_string(length=6, allowed_chars='0123456789')

            # Borrar códigos anteriores y guardar nuevo
            PasswordResetCode.objects.filter(email=email).delete()
            PasswordResetCode.objects.create(
            email=email, 
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
            )
            
        def test_email():
            # Enviar correo
            try:
                send_mail(
                    'Código de recuperación de contraseña',
                    f'Tu código de recuperación es: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                # Log the error
                print(f"Error sending email: {str(e)}")
                return Response(
                    {'error': f'Error enviando correo: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            test_email()

            return Response({'message': 'Se ha enviado un código de recuperación a tu correo.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class PasswordResetVerifyView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        verify_only = request.data.get('verify_only', False)
        
        # Validar campos requeridos
        if not all([email, code]):
            return Response(
                {"detail": "Email and code are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar usuario y código
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
            {"detail": "Usuario no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
        reset_code = PasswordResetCode.objects.filter(
            email=email, 
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not reset_code:
            return Response(
                {"detail": "Código incorrecto o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si es solo verificación
        if verify_only:
            return Response(
                {"detail": "Código válido"},
                status=status.HTTP_200_OK
            )
        
        # Validar nueva contraseña
        if not new_password or len(new_password) < 6:
            return Response(
                {"detail": "La contraseña debe tener al menos 6 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar contraseña
        user.set_password(new_password)
        user.save()
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