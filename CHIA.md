# CHIA Hito 4 Global Exchange

## 1. Objetivo del documento

Este documento registra las principales conversaciones mantenidas con una herramienta de inteligencia artificial durante el Sprint 2 del proyecto Global Exchange. La IA fue utilizada como apoyo para analizar requerimientos, proponer estructuras de implementación, resolver errores técnicos y preparar pruebas y documentación. Las propuestas fueron revisadas, adaptadas y verificadas dentro del entorno del proyecto antes de ser incorporadas.

## 2. Contexto del trabajo

El proyecto utiliza Django, PostgreSQL, Docker Compose y Keycloak. Durante el Hito 4 se trabajó principalmente en el CRUD de medios de pago del cliente, la vinculación entre usuarios y clientes, las pruebas unitarias y la documentación del código fuente con Sphinx.

## 3. Consultas y resultados principales

### 3.1 Diseño del CRUD de medios de pago

**Consulta realizada:** Se solicitó orientación para implementar el CRUD de medios de pago y determinar su relación con Keycloak y con el modelo de clientes de Django.

**Orientación recibida:** Se aclaró que Keycloak debía encargarse de la autenticación y de los roles, mientras que los clientes comerciales y sus medios de pago debían mantenerse en la base de datos de la aplicación. Inicialmente se evaluó Stripe, pero se decidió implementar un CRUD local debido al alcance académico del sprint y a las limitaciones de disponibilidad del servicio.

**Decisión aplicada:** Se creó una aplicación Django independiente denominada `payments`, relacionada con `apps.clientes.models.Cliente`. El modelo almacena tipo, alias, titular, marca, últimos cuatro dígitos, vencimiento, estado y condición de medio predeterminado. Por seguridad, no se almacena el número completo de tarjeta ni el código CVV.

### 3.2 Vistas, formularios y permisos

**Consulta realizada:** Se pidió una propuesta de vistas y formularios para crear, consultar, editar y eliminar medios de pago.

**Orientación recibida:** Se propusieron vistas basadas en funciones protegidas con `login_required`, un `ModelForm` con validaciones y consultas limitadas al cliente vinculado al usuario autenticado.

**Decisión aplicada:** Las vistas verifican que exista un `UserClientLink` con estado `APPROVED`. Además, al consultar, editar o eliminar un registro, se filtra por el cliente vinculado para impedir el acceso a medios de pago de otros clientes. La selección de un nuevo medio predeterminado desmarca el anterior dentro de una transacción.

### 3.3 Interfaz visual

**Consulta realizada:** Se solicitó adaptar las pantallas del CRUD al estilo visual lila utilizado por Global Exchange.

**Orientación recibida:** Se propusieron plantillas reutilizables con una base común, tarjetas para representar los medios de pago y botones diferenciados para registrar, editar y eliminar.

**Corrección realizada:** Durante la integración se detectó que el contenido del listado había sido colocado accidentalmente en `base.html`, haciendo que la plantilla se extendiera a sí misma. El error `TemplateDoesNotExist` se corrigió separando correctamente `base.html`, `lista.html`, `formulario.html` y `confirmar_eliminacion.html`.

### 3.4 Migraciones de Django

**Consulta realizada:** Se analizaron errores producidos al retirar campos relacionados con Stripe y aplicar nuevas migraciones.

**Orientación recibida:** Se revisó el historial de migraciones y se identificó que una migración intentaba eliminar una columna que ya no existía en PostgreSQL. Después de verificar que la operación solo representaba ese estado ya alcanzado, la migración se marcó como aplicada y se continuó con el resto.

**Verificación:** Se ejecutaron `makemigrations`, `migrate`, `showmigrations` y `check` hasta obtener una configuración consistente y sin errores del sistema.

### 3.5 Pruebas unitarias

**Consulta realizada:** Se pidió una estrategia de pruebas para el CRUD.

**Orientación recibida:** Se propusieron pruebas del modelo, del formulario, de las vistas y de los permisos utilizando `django.test.TestCase`.

**Cobertura implementada:**

- Creación y representación textual de un medio de pago.
- Validación de los últimos cuatro dígitos.
- Rechazo de fechas de vencimiento pasadas.
- Visualización de medios de pago del cliente.
- Creación, modificación y eliminación desde las vistas.
- Existencia de un único medio predeterminado.
- Redirección de usuarios no autenticados.
- Rechazo de usuarios sin una vinculación aprobada.

Al ejecutar inicialmente las pruebas de vistas se obtuvieron respuestas HTTP 302 en lugar de 200. Se determinó que `mozilla_django_oidc.middleware.SessionRefresh` redirigía las sesiones creadas con `force_login()` hacia Keycloak. Para aislar las pruebas unitarias, el middleware de renovación OIDC se excluyó únicamente durante dichas pruebas mediante `override_settings`. La autenticación real de la aplicación no fue modificada.

### 3.6 Documentación con Sphinx

**Consulta realizada:** Se solicitó configurar documentación automática del código fuente.

**Orientación recibida:** Se configuraron las extensiones `autodoc`, `napoleon` y `viewcode`, junto con el tema `sphinx_rtd_theme`. También se configuró Django dentro de `conf.py` para que Sphinx pudiera importar los módulos de la aplicación.

**Decisión aplicada:** Se utilizó el constructor `singlehtml` para obtener una documentación continua que pueda recorrerse mediante desplazamiento. Los modelos, formularios y vistas incorporan docstrings en español, y la documentación puede reconstruirse con:

```powershell
docker compose exec web python -m sphinx -E -a -b singlehtml docs/source docs/build/singlehtml
```

### 3.7 Control de versiones

**Consulta realizada:** Se consultó cómo integrar la rama de funcionalidad en `develop` y cómo evitar conflictos producidos por archivos `__pycache__`.

**Orientación recibida:** Se indicó agregar `__pycache__/` y `*.py[cod]` al archivo `.gitignore`, retirar los archivos generados que Git ya rastreaba y realizar el merge desde `develop`.

**Resultado:** Los archivos temporales de Python fueron excluidos y la rama de funcionalidad pudo integrarse en `develop`.

## 4. Validación realizada por el equipo

Las respuestas de la IA se utilizaron como propuestas técnicas y no como resultados aceptados automáticamente. Durante el trabajo se realizaron las siguientes verificaciones:

- Revisión de nombres reales de aplicaciones, modelos, campos y rutas.
- Ejecución del proyecto mediante Docker Compose.
- Aplicación y revisión del historial de migraciones.
- Pruebas manuales del CRUD con usuarios vinculados.
- Revisión visual de las plantillas.
- Ejecución de pruebas unitarias.
- Generación y revisión de la documentación HTML de Sphinx.
- Revisión de cambios con Git antes del merge.

## 5. Conclusión

La herramienta de IA sirvió como apoyo para acelerar el análisis, ofrecer ejemplos de implementación y diagnosticar errores. El equipo mantuvo la responsabilidad de decidir el alcance final, adaptar las propuestas a la arquitectura existente, ejecutar las pruebas y validar la integración del trabajo en el repositorio.
