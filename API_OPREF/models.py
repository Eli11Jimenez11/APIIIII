from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import datetime

# validar la fecha de finalización no sea mayor a 30 días
def validate_fecha_finalizacion(value):
    fecha_actual = timezone.now().date()
    fecha_minima = fecha_actual + datetime.timedelta(days=30)

    if value < fecha_minima:
        raise ValidationError(
            f"La fecha de finalización debe ser al menos un mes después de hoy (fecha mínima permitida: {fecha_minima})."
        )

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Cotizacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Contrato(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('firmado', 'Firmado'),
        ('en_proceso', 'En proceso'),
        ('finalizado', 'Finalizado'),
        ('anulado', 'Anulado'),
    ]

    fecha_inicio = models.DateField()  # Campo añadido para empatar con fromJson
    fecha_finalizacion = models.DateField(validators=[validate_fecha_finalizacion])
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    nombre_proyecto = models.CharField(max_length=255)
    descripcion_proyecto = models.TextField()
    cotizacion = models.ForeignKey('Cotizacion', on_delete=models.SET_NULL, null=True)
    servicio = models.ForeignKey('Servicio', on_delete=models.SET_NULL, null=True)
    total = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nombre_proyecto

class Novedad(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)

# recuperar contraseña
class PasswordResetCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10) 

    def __str__(self):
        return f"{self.email} - {self.code}"
    
class PasswordResetPassword(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    password = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10) 

    def __str__(self):
        return f"{self.email} - {self.code}"
