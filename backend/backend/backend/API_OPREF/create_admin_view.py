from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View

class CreateAdminView(View):
    def get(self, request):
        User = get_user_model()
        
        if not User.objects.filter(email="admin2@gmail.com").exists():
            user = User.objects.create_user(
                email="admin2@gmail.com",
                password="admin12345"
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return JsonResponse({'message': 'Superusuario creado correctamente.'})
        else:
            return JsonResponse({'message': 'Ya existe un superusuario.'})
