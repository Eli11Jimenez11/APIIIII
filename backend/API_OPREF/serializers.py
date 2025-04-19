from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Contrato, Cotizacion, Servicio, Novedad
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

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
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # Esto indica que el "username" será el email

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Debe proporcionar tanto el correo como la contraseña.')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Correo electrónico o contraseña incorrectos.')

        if not user.check_password(password):
            raise serializers.ValidationError('Correo electrónico o contraseña incorrectos.')

        if not user.is_active:
            raise serializers.ValidationError('El usuario está inactivo.')

        # Super() llama a TokenObtainPairSerializer y genera los tokens automáticamente
        data = super().validate(attrs)

        # Extra: Podés agregar más datos al payload si querés
        data.update({
            'user_id': user.id,
            'email': user.email,
        })

        return data

        
