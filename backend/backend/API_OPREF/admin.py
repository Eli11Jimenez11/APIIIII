from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import User, Cotizacion, Servicio, Contrato, Novedad, PasswordResetCode

class UserCreationForm(forms.ModelForm):
    """Formulario para crear nuevos usuarios."""
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Importante
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Formulario para actualizar usuarios existentes."""
    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_staff', 'is_superuser')

class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = ('email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )

# Ahora registra bien el User
admin.site.register(User, UserAdmin)

# Y los otros modelos como ya tenías
admin.site.register(Cotizacion)
admin.site.register(Servicio)
admin.site.register(Contrato)
admin.site.register(Novedad)
admin.site.register(PasswordResetCode)
