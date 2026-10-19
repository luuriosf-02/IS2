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

# Registro de Interacción con IA (CHIA) - Sprint 4

## Proyecto: Global Exchange
**Sprint:** 4  
**Fecha:** Octubre 2026  

---

### Consulta 1: Integración de pasarelas de pago (SIPAP y Stripe)
- **Prompt:** ¿Cómo estructurar el servicio de validación de pagos para soportar tanto transferencias locales SIPAP (con comprobante digital) como cargos internacionales vía Stripe?
- **Respuesta IA:** Se propuso un patrón de servicios separados (`PaymentProcessorService`) con métodos estáticos independientes para SIPAP (que conmuta el estado a `PENDING_VALIDATION`) y Stripe (que procesa cobros en línea de manera síncrona), asegurando el control de excepciones ante fallos de cobro.

### Consulta 2: Notificaciones automáticas por variaciones de tasa
- **Prompt:** ¿Cómo disparar alertas en tiempo real y correos automáticos cuando el Administrador actualiza las tasas de cambio de las divisas?
- **Respuesta IA:** Se sugirió encapsular la lógica de actualización en un método de servicio que invoque simultáneamente al canal de WebSockets (`channels`) para la actualización in-app en pantalla y a la función de correo de Django (`send_mail`).

### Consulta 3: Pruebas unitarias para el Módulo de Caja y Control de Integridad
- **Prompt:** ¿Cómo escribir una prueba unitaria en Django que valide que los movimientos de caja no puedan ser eliminados físicamente (cumpliendo con RNF09)?
- **Respuesta IA:** Se implementó una prueba utilizando `self.assertRaises(NotImplementedError)` para asegurar que el método `delete()` del modelo `CashMovement` arroje una excepción y bloquee cualquier intento de borrado físico.