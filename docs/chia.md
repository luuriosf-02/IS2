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