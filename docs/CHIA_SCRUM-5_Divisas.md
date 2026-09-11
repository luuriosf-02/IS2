# Módulo de Gestión de Divisas y Tasas de Cambio (SCRUM-5)

## Descripción General
Este módulo permite la administración, registro y control de las tasas de cambio de diferentes divisas dentro del sistema. Está diseñado para garantizar la seguridad mediante control de acceso por roles (RBAC) y mantener un registro de auditoría transparente de cada modificación realizada.

---

## Componentes Técnicos

### 1. Modelos (`models.py`)
El módulo utiliza principalmente el modelo `TasaCambio`, vinculado relacionalmente con el catálogo de monedas:
* **`moneda`**: Clave foránea (`ForeignKey`) hacia el modelo `Moneda`, estableciendo la relación con el código y nombre de la divisa.
* **`tasa_compra`**: Campo decimal (`DecimalField` con `max_digits=12` y `decimal_places=4`) para registrar el precio de adquisición.
* **`tasa_venta`**: Campo decimal (`DecimalField` con `max_digits=12` y `decimal_places=4`) para registrar el precio de salida.
* **`fecha_actualizacion`**: Marca temporal automática (`auto_now=True`) que registra el momento exacto de la última modificación.
* **`usuario_modificador`**: Relación con el usuario del sistema responsable de registrar o actualizar la cotización.

---

### 2. Lógica y Control de Acceso (`views.py`)
* **Autenticación obligatoria**: Decorador `@login_required` para asegurar que solo usuarios con sesión activa accedan al endpoint.
* **RBAC (Control de Acceso Basado en Roles)**: 
  * Se valida si el usuario pertenece al grupo **"Analista Cambiario"** o cuenta con privilegios de superusuario (`is_superuser`).
  * En caso de no cumplir con los permisos, el sistema responde de forma segura con una vista de acceso denegado (`403.html`).
* **Procesamiento de Formularios (`POST`)**: Captura manual y segura de los datos enviados desde la interfaz para asociarlos y guardarlos en la base de datos de manera atómica.

---

### 3. Interfaz de Usuario y Plantillas (`gestion_tasas.html`)
* **Formulario de Actualización**: Selectores desplegables dinámicos para elegir la divisa e inputs numéricos con soporte para precisión decimal (`step="0.0001"`).
* **Filtros de Visualización**: Uso de filtros de plantillas nativos de Django (`|floatformat:"-2"`) para asegurar una presentación limpia de los montos en la tabla principal.
* **Tabla de Cotizaciones Vigentes**: Listado en tiempo real que detalla la moneda, los valores de compra y venta, la hora de actualización y el usuario autor de la modificación.

---

## Pruebas y Validación
* **Integridad de Base de Datos**: Verificado mediante el shell de Django y consultas a los registros persistidos.
* **Control de Versiones**: Desarrollo aislado en la rama `feature/SCRUM-5` e integrado mediante Pull Request hacia el repositorio principal.