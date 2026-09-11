# Reporte de Calidad de Software (QA) y Pruebas Unitarias - Sprint 2

## 1. Alcance Evaluado (Sprint 2)
- [x] CRUD de Monedas
- [x] CRUD de Cotizaciones (Tasas de compra y venta)
- [x] CRUD de Medios de Pago Cliente
- [x] Visualización de Tasas
- [x] Simulador de Conversión

## 2. Ejecución de Pruebas Unitarias (PUD)
Pruebas automatizadas sobre los modelos y controladores de la aplicación `dashboard`.

- **Módulos Probados:** `app.apps.dashboard`
- **Total de Pruebas:** 8 ejecutadas
- **Estado:** PASS (0 Errores, 0 Fallos)

### Resumen de Clases de Prueba:
1. `MonedasYCotizacionesTestCase`: Pruebas sobre la gestión de divisas y tasas aplicadas.
2. `MediosPagoTestCase`: Validación de medios de pago activos e inactivos.
3. `SimuladorConversionTestCase`: Verificación matemática de la conversión de divisas.

## 3. Cobertura de Código y Calidad (QA)
- **Cobertura General:** 85%
- **Comando de Ejecución:** `coverage run --source='app/apps' manage.py test app/apps`