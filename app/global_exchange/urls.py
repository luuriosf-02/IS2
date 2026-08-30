"""
URL configuration for global_exchange project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from django.http import HttpResponse
from apps.dashboard.views import home, custom_logout

# def home(request):
#     if request.user.is_authenticated:
#         html = f"""
#             <h1>Bienvenido, {request.user.first_name} {request.user.last_name}!</h1>
#             <p>Has iniciado sesión correctamente a través de Keycloak.</p>
#             <a href="/oidc/logout/">Cerrar Sesión</a>
#         """
#     else:
#         html = """
#             <h1>Página Pública de Prueba</h1>
#             <p>No has iniciado sesión.</p>
#             <a href="/oidc/authenticate/">Iniciar Sesión con Keycloak</a>
#         """
#     return HttpResponse(html)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('logout/', custom_logout,name='logout'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('users/', include('apps.users.urls')),
]
