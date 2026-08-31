"""
URL configuration for global_exchange project.
"""

from django.contrib import admin
from django.urls import path, include

from apps.dashboard.views import home, custom_logout


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('logout/', custom_logout, name='logout'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('users/', include('apps.users.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')), # URLs automáticas para login/logout
    path('clientes/', include('apps.clientes.urls')), # URLs de la app clientes
]
