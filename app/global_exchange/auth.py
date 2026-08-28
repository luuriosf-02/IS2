from mozilla_django_oidc.auth import OIDCAuthenticationBackend

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
        
        # Extraemos roles de prueba
        realm_access = claims.get('realm_access', {})
        print(realm_access)
        roles = realm_access.get('roles', [])
        
        print("Roles encontrados:", roles) # Para ver qué trae exactamente
        
        if len(roles) > 0:
            user.role = roles[0]
        else:
            user.role = 'Cliente'
            
        user.save()