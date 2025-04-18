from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomAuthTokenSerializer
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone 
from datetime import timedelta
from .models import Contrato, Cotizacion, Servicio, Novedad, PasswordResetCode
from .serializers import (
    ContratoSerializer, CotizacionSerializer, ServicioSerializer, NovedadSerializer, PasswordResetRequestSerializer, PasswordResetVerifySerializer
)
from django.contrib.auth import get_user_model
User = get_user_model()

def home(request):
    return JsonResponse({'mensaje': 'API OPREF funcionando correctamente 🚀'})

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
            
            if not User.objects.filter(email=email).exists():
                return Response({"detail": "Correo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

            if PasswordResetCode.objects.filter(email=email, created_at__gt=timezone.now()-timedelta(minutes=10)).exists():
                return Response({"detail": "Ya se ha enviado un código de recuperación recientemente. Intenta nuevamente en unos minutos."}, status=status.HTTP_400_BAD_REQUEST)

            code = get_random_string(length=6, allowed_chars='0123456789')
            reset_code = PasswordResetCode.objects.create(email=email, code=code)

            send_mail(
                'Código de recuperación de contraseña',
                f'Tu código de recuperación es: {code}',
                'no-reply@opref.com',
                [email],
                fail_silently=False,
            )

            return Response({"detail": "Código de recuperación enviado al correo"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifyView(APIView):
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']

            try:
                # Verifica si el código es válido
                reset_code = PasswordResetCode.objects.get(email=email, code=code)

                if reset_code.is_expired():
                    return Response({"detail": "El código ha expirado"}, status=status.HTTP_400_BAD_REQUEST)

                # Cambia la contraseña del usuario
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()

                # Borra el código de la base de datos
                reset_code.delete()

                return Response({"detail": "Contraseña actualizada con éxito"}, status=status.HTTP_200_OK)

            except PasswordResetCode.DoesNotExist:
                return Response({"detail": "Código incorrecto o no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({"detail": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class CustomTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Autenticamos al usuario directamente
            user = authenticate(username=email, password=password)
            if user is None:
                return Response({'detail': 'Correo electrónico o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

            # Generamos el token JWT
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)