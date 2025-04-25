from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Contrato, Cotizacion, Servicio, Novedad, PasswordResetCode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class CotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizacion
        fields = '__all__'

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrato
        fields = '__all__'

class NovedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Novedad
        fields = '__all__'

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    
class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email is None or password is None:
            logger.debug(f"Faltan credenciales: email={email}, password={'sí' if password else 'no'}")
            raise serializers.ValidationError('Debe proporcionar tanto el correo como la contraseña.')
        
        user = authenticate(request=self.context.get('request'), email=email, password=password)
        
        if not user:
            logger.debug(f'Falló autenticación para email: {email}')
            raise serializers.ValidationError('Correo electrónico o contraseña incorrectos.')

        if not user.is_active:
            logger.debug(f'Usuario inactivo: {email}')
            raise serializers.ValidationError('El usuario está inactivo.')

        data['user'] = user
        return data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

        
