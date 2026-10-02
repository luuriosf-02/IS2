# IS2
SCRUM Global Exchange

### Usuarios para keycloak en la configuración exportada
- admin: 1234 (administrador)
- ana: 1234 (analista)
- lujan: 123
- user0: 1234 (cliente-usuario)

### Para iniciar el contenedor ejecutar:
- docker compose up (opcionalmente se puede usar la bandera -d o --build para forzar construcción de imagen)

### Importante
Keycloak usa su configuración local existente si ya existe, para borrarla e importar la configuración
de este repositorio en caso de tener otra o si está desactualizada (./keycloak-export/global_exchange-realm.json) se debe ejecutar:
- docker compose down -v

 ➡️ *La bandera -v es para borrar los volúmenes, entre ellos la configuración persistente de Keycloak*
