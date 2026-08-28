# apps/dashboard/views.py (o donde tengas tus vistas)
from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout

def home(request):
    # Django ya inyecta `request.user` gracias a Keycloak y la autenticación
    return render(request, 'dashboard.html', {'user': request.user})

def custom_logout(request):
    # 1. Cierra la sesión localmente en Django
    django_logout(request)
    
    # 2. Configura los datos de tu servidor Keycloak
    # (Reemplaza estos valores con la URL de tu Keycloak, tu realm y tu client_id)
    KEYCLOAK_URL = "http://localhost:8080/realms/global_exchange/protocol/openid-connect/logout"
    CLIENT_ID = "django_client"
    
    # URL a la que Keycloak devolverá al usuario después de cerrar sesión (la página principal de tu app)
    redirect_uri = request.build_absolute_uri('/')
    
    # 3. Construye la URL de cierre de sesión global de Keycloak
    keycloak_logout_url = (
        f"{KEYCLOAK_URL}"
        f"?client_id={CLIENT_ID}"
        f"&post_logout_redirect_uri={redirect_uri}"
    )
    
    # 4. Redirige al usuario a Keycloak para destruir su sesión allá también
    return redirect(keycloak_logout_url)