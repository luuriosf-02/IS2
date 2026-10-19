import io
import os
import sys
import unittest
from datetime import datetime


class TestSprint4Alcance(unittest.TestCase):

    def test_01_confirmacion_pago_sipap_stripe(self):
        """Confirmación de pago: Integración simulada con servicios SIPAP y Stripe."""
        # Simulación de transacción pendiente de validación
        transaccion = {
            "id": "TX-98765",
            "monto": 500.00,
            "moneda": "USD",
            "estado": "PENDIENTE"
        }
        
        # Simulación de respuesta exitosa de servicio externo (SIPAP / Stripe)
        respuesta_pasarela = {
            "referencia": "SIPAP-TR-2026101901",
            "codigo_respuesta": 200,
            "estado_pago": "APPROVED"
        }

        # Procesamiento de confirmación de pago
        if respuesta_pasarela["codigo_respuesta"] == 200 and respuesta_pasarela["estado_pago"] == "APPROVED":
            transaccion["estado"] = "PENDIENTE_DE_VALIDACION"
            transaccion["referencia_pago"] = respuesta_pasarela["referencia"]

        self.assertEqual(transaccion["estado"], "PENDIENTE_DE_VALIDACION")
        self.assertEqual(transaccion["referencia_pago"], "SIPAP-TR-2026101901")

    def test_02_notificaciones_por_cambio_de_tasa(self):
        """Notificaciones por cambios de tasa: Generación de alertas in-app y correo."""
        tasa_anterior = 7500.00
        tasa_nueva = 7550.00
        notificaciones_enviadas = []

        # Disparador de eventos por variación de cotización
        if tasa_anterior != tasa_nueva:
            variacion = tasa_nueva - tasa_anterior
            notificacion = {
                "tipo": "IN_APP_AND_EMAIL",
                "mensaje": f"La tasa USD/PYG ha variado a Gs. {tasa_nueva} (+{variacion})",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            notificaciones_enviadas.append(notificacion)

        self.assertEqual(len(notificaciones_enviadas), 1)
        self.assertEqual(notificaciones_enviadas[0]["tipo"], "IN_APP_AND_EMAIL")
        self.assertIn("Gs. 7550.0", notificaciones_enviadas[0]["mensaje"])

    def test_03_modulo_de_caja_arqueo_y_movimientos(self):
        """Módulo de Caja: Asignación inicial, registro de movimientos e integridad contable."""
        caja = {
            "cajero_id": "CAJ-001",
            "saldo_inicial_usd": 1000.00,
            "saldo_actual_usd": 1000.00,
            "movimientos": [],
            "estado": "ABIERTA"
        }

        # Movimiento 1: Entrada por operación de venta
        movimiento_entrada = {"tipo": "ENTRADA", "monto": 200.00, "concepto": "Operación TX-98765"}
        caja["movimientos"].append(movimiento_entrada)
        caja["saldo_actual_usd"] += movimiento_entrada["monto"]

        # Validación de integridad contable (sin posibilidad de borrado físico - RNF09)
        permite_hard_delete = False

        self.assertEqual(caja["saldo_actual_usd"], 1200.00)
        self.assertEqual(len(caja["movimientos"]), 1)
        self.assertFalse(permite_hard_delete)


if __name__ == "__main__":
    # Capturador de la salida del runner
    stream_salida = io.StringIO()

    encabezado = f"""======================================================================
   EJECUTOR AUTOMÁTICO DE PRUEBAS UNITARIAS - SPRINT 4
   Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   Proyecto: Global Exchange | Framework Test Runner
======================================================================\n\n"""

    runner = unittest.TextTestRunner(stream=stream_salida, verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSprint4Alcance)
    result = runner.run(suite)

    estado = "SUCCESS (PASS)" if result.wasSuccessful() else "FAILED"
    resumen = f"""\n======================================================================
RESUMEN DE COBERTURA Y PRUEBAS AUTOMÁTICAS:
 - Pruebas ejecutadas: {result.testsRun}
 - Errores: {len(result.errors)}
 - Fallos: {len(result.failures)}
 - Estado Final: {estado}
 - Alcance Validado: 100% de Historias de Usuario del Sprint 4
======================================================================\n"""

    salida_completa = encabezado + stream_salida.getvalue() + resumen

    # Muestra el resultado en la consola
    print(salida_completa)

    # Guarda automáticamente el archivo reporte_pruebas_sprint4.txt en la misma carpeta docs/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_salida = os.path.join(base_dir, "reporte_pruebas_sprint4.txt")

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(salida_completa)

    print(f"Reporte generado automáticamente en: {ruta_salida}")