from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from apps.users.models import Profile

class MyOIDCAB(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        # Este método se ejecuta siempre y valida los claims. 
        # Aquí podemos guardar los claims temporalmente en el objeto para usarlos al crear/actualizar.
        return super().verify_claims(claims)

    def create_user(self, claims):
        print("--- CREANDO USUARIO ---", claims) # Ahora sí debería salir en consola
        user = super().create_user(claims)
        self._sync_user_data(user, claims)
        return user

    def update_user(self, user, claims):
        print("--- ACTUALIZANDO USUARIO ---", claims) # Y este al iniciar sesión de nuevo
        user = super().update_user(user, claims)
        self._sync_user_data(user, claims)
        return user

    def _sync_user_data(self, user, claims):
        user.username = claims.get('preferred_username', user.username)
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')
        user.save() # Guardamos el usuario base

        # Extraemos roles
        realm_access = claims.get('realm_access', {})
        roles = set(realm_access.get('roles', []))
        for client_access in claims.get('resource_access', {}).values():
            roles.update(client_access.get('roles', []))
        if "Cliente" in roles:
            role_asignado = "Cliente"
        elif "Analista Cambiario" in roles:
            role_asignado = "Analista Cambiario"
        elif "Cajero" in roles:
            role_asignado = "Cajero"
        elif "Contador" in roles:
            role_asignado = "Contador"
        elif "Administrador" in roles:
                    role_asignado = "Administrador"
        else:
            role_asignado = "No registrado"
        print(role_asignado)
        # Creamos o actualizamos el perfil asociado
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = role_asignado
        profile.save()