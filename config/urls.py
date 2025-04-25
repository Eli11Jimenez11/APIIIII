from django.contrib import admin
from django.urls import path, include
from API_OPREF.views import home, health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('api/', include('API_OPREF.urls')),
    path('health/', health_check),
]