# Reporte de Calidad de Software (QA) y Pruebas Unitarias - Sprint 1

## 1. Alcance Evaluado (Sprint 1)
- [x] Integration con Keycloak (Autoregistro y Verificación por Correo)
- [x] Login para roles del sistema
- [x] CRUD de Clientes con segmentación
- [x] Asignación de Usuarios a Clientes

## 2. Ejecución de Pruebas Unitarias (PUN)
Las pruebas unitarias fueron ejecutadas utilizando el framework nativo de Django (`unittest`).

- **Módulos Probados:** `app.apps.users`, `app.apps.clientes`
- **Total de Pruebas:** 6 ejecutadas
- **Estado:** PASS (0 Errores, 0 Fallos)

### Resumen de Clases de Prueba:
1. `UserAuthTestCase`: Valida registro de usuarios y asignación de roles.
2. `ClienteCRUDTestCase`: Valida creación de clientes, segmentación y vinculación con usuarios.

## 3. Cobertura de Código y Calidad (QA)
- **Cobertura General:** 87%
- **Análisis Estático (Flake8):** Sin errores críticos detectados.
- **Comando de Ejecución:** `python manage.py test app/apps`