from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout


def home(request):
    es_analista = False

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        es_grupo_analista = request.user.groups.filter(name__icontains='analista').exists()
        es_usuario_analista = request.user.username.lower() in ['analista', 'analista cambiario']
        es_analista = (
            bool(profile and profile.role == 'Analista Cambiario')
            or es_grupo_analista
            or es_usuario_analista
            or request.user.is_superuser
        )

    return render(request, 'dashboard.html', {
        'user': request.user,
        'es_analista': es_analista,
    })


def custom_logout(request):
    django_logout(request)

    KEYCLOAK_URL = "http://localhost:8080/realms/global_exchange/protocol/openid-connect/logout"
    CLIENT_ID = "django_client"
    redirect_uri = request.build_absolute_uri('/')

    keycloak_logout_url = (
        f"{KEYCLOAK_URL}"
        f"?client_id={CLIENT_ID}"
        f"&post_logout_redirect_uri={redirect_uri}"
    )

    return redirect(keycloak_logout_url)