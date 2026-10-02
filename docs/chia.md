# CHIA - Documentación de Interacción con IA (Sprint 1)

## Datos del Proyecto
- **Sprint:** Sprint 1 - Proyecto Global Exchange
- **Asistente:** AI Assistant / ChatGPT / Gemini

## Registro de Conversaciones

### Consulta 1: Integración de Keycloak con Django
- **Prompt:** "¿Cómo configurar el middleware de autenticación en Django para capturar el token JWT enviado por Keycloak?"
- **Resultado:** Se generó la estructura base para validar claims en `global_exchange/auth.py`.

### Consulta 2: Estructura de Modelos y Pruebas para Clientes
- **Prompt:** "Generar prueba unitaria en Django para verificar la creación de un cliente con segmento 'Corporativo'."
- **Resultado:** Se creó el archivo de pruebas en `app/apps/clientes/tests.py` validando la persistencia en base de datos.

# CHIA - Documentación de Interacción con IA (Sprint 2)

## Datos del Proyecto
- **Sprint:** Sprint 2 - Proyecto Global Exchange
- **Asistente:** AI Assistant / ChatGPT / Gemini

## Registro de Conversaciones

### Consulta 1: Lógica del Simulador de Cotizaciones
- **Prompt:** "Necesito una función para calcular la conversión entre moneda origen y destino aplicando el precio de venta o compra actual."
- **Resultado:** Se implementó la lógica en la vista/servicio del simulador en `app/apps/dashboard`.

### Consulta 2: Generación de Pruebas Unitarias para el Sprint 2
- **Prompt:** "¿Cómo hacer unit tests en Django para verificar que un cálculo de conversión con decimales sea preciso?"
- **Resultado:** Se integró `Decimal` en `test_simulador.py` para evitar errores de redondeo de punto flotante.

# Registro de Interacción con IA (CHIA) - Sprint 3

## Proyecto: Global Exchange
**Sprint:** 3  
**Fecha:** Octubre 2026  

---

### Consulta 1: Cálculo de comisiones y tasas
- **Prompt:** ¿Cómo estructurar el cálculo de comisión y la fijación de tasa de cambio al momento de crear la transacción?
- **Respuesta IA:** Se recomendó congelar el valor de la tasa de cambio en la fila de la transacción (`tasa_aplicada`) y calcular el monto final agregando una comisión porcentual configurable antes de procesar el pago.

### Consulta 2: Cancelación por cambio de cotización
- **Prompt:** Implementación de la vista para abortar una transacción si la cotización cambia antes de abonar.
- **Respuesta IA:** Se diseñó un endpoint `/transaccion/<id>/cancelar/` que compara la tasa registrada en la transacción contra la tasa activa en tiempo real de la divisa antes de confirmar la operación.

### Consulta 3: Historial de transacciones de solo lectura
- **Prompt:** ¿Cómo garantizar que el historial de transacciones sea exclusivamente de consulta?
- **Respuesta IA:** Restringir la vista para responder únicamente a peticiones `GET` y no exponer endpoints de modificación (`POST`/`PUT`/`DELETE`) sobre transacciones finalizadas o registradas.