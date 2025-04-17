from django.contrib import admin
from .models import User, Cotizacion, Servicio, Contrato, Novedad, PasswordResetCode

# Registra los modelos
admin.site.register(User)
admin.site.register(Cotizacion)
admin.site.register(Servicio)
admin.site.register(Contrato)
admin.site.register(Novedad)
admin.site.register(PasswordResetCode)