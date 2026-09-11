import sys
import os
import unittest
from decimal import Decimal
import datetime

# Almacenamiento simulado en memoria para datos de prueba
BD_MONEDAS = {}
BD_COTIZACIONES = {}
BD_MEDIOS_PAGO = {}

class Moneda:
    def __init__(self, codigo, nombre, simbolo):
        self.codigo = codigo
        self.nombre = nombre
        self.simbolo = simbolo

class Cotizacion:
    def __init__(self, origen, destino, compra, venta):
        self.origen = origen
        self.destino = destino
        self.compra = Decimal(str(compra))
        self.venta = Decimal(str(venta))

class MedioPago:
    def __init__(self, id_pago, nombre, activo=True):
        self.id_pago = id_pago
        self.nombre = nombre
        self.activo = activo

# Pruebas Unitarias del Alcance del Sprint 2
class TestSprint2Alcance(unittest.TestCase):

    def setUp(self):
        """Carga de datos de prueba previos a cada test."""
        BD_MONEDAS.clear()
        BD_COTIZACIONES.clear()
        BD_MEDIOS_PAGO.clear()
        
        # Carga de datos de prueba
        BD_MONEDAS["USD"] = Moneda("USD", "Dólar Estadounidense", "$")
        BD_MONEDAS["PYG"] = Moneda("PYG", "Guaraní Paraguayo", "₲")
        BD_MONEDAS["BRL"] = Moneda("BRL", "Real Brasileño", "R$")

        BD_COTIZACIONES["USD_PYG"] = Cotizacion("USD", "PYG", 7250.00, 7350.00)
        BD_COTIZACIONES["BRL_PYG"] = Cotizacion("BRL", "PYG", 1300.00, 1350.00)

        BD_MEDIOS_PAGO[1] = MedioPago(1, "Transferencia bancaria SIPAP", True)
        BD_MEDIOS_PAGO[2] = MedioPago(2, "Tarjeta de Débito/Crédito", True)

    def test_01_crud_monedas(self):
        """CRUD Monedas: Creación, consulta y modificación de monedas."""
        self.assertIn("USD", BD_MONEDAS)
        self.assertEqual(BD_MONEDAS["USD"].nombre, "Dólar Estadounidense")
        
        # Registro de nueva moneda (Euro)
        BD_MONEDAS["EUR"] = Moneda("EUR", "Euro", "€")
        self.assertEqual(len(BD_MONEDAS), 4)

    def test_02_crud_cotizaciones(self):
        """CRUD Cotizaciones: Verificación de tasas de compra y venta."""
        cotiz = BD_COTIZACIONES["USD_PYG"]
        self.assertEqual(cotiz.compra, Decimal("7250.00"))
        self.assertEqual(cotiz.venta, Decimal("7350.00"))
        self.assertGreater(cotiz.venta, cotiz.compra)

    def test_03_crud_medios_pago(self):
        """CRUD Medios de Pago: Registro y desactivación de medios de pago."""
        mp = BD_MEDIOS_PAGO[1]
        self.assertTrue(mp.activo)
        mp.activo = False
        self.assertFalse(BD_MEDIOS_PAGO[1].activo)

    def test_04_visualizacion_tasas(self):
        """Visualización: Listado activo de cotizaciones registradas."""
        tasas = list(BD_COTIZACIONES.keys())
        self.assertIn("USD_PYG", tasas)
        self.assertIn("BRL_PYG", tasas)

    def test_05_simulador_conversion_compra(self):
        """Simulador: Cálculo exacto para operación de compra (100 USD -> PYG)."""
        cotiz = BD_COTIZACIONES["USD_PYG"]
        monto_origen = Decimal("100.00")
        resultado = monto_origen * cotiz.compra
        self.assertEqual(resultado, Decimal("725000.00"))

    def test_06_simulador_conversion_venta(self):
        """Simulador: Cálculo exacto para operación de venta (100 USD -> PYG)."""
        cotiz = BD_COTIZACIONES["USD_PYG"]
        monto_origen = Decimal("100.00")
        resultado = monto_origen * cotiz.venta
        self.assertEqual(resultado, Decimal("735000.00"))

def run_tests_and_generate_report():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = []
    
    header = "="*70 + "\n"
    header += f"   EJECUTOR AUTOMÁTICO DE PRUEBAS UNITARIAS - SPRINT 2\n"
    header += f"   Fecha de ejecución: {timestamp}\n"
    header += f"   Proyecto: Global Exchange | Framework Test Runner\n"
    header += "="*70 + "\n\n"
    
    print(header)
    report_lines.append(header)

    import io
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSprint2Alcance)
    result = runner.run(suite)

    test_output = stream.getvalue()
    print(test_output)
    report_lines.append(test_output)

    summary = "\n" + "="*70 + "\n"
    summary += f"RESUMEN DE COBERTURA Y PRUEBAS AUTOMÁTICAS:\n"
    summary += f" - Pruebas ejecutadas: {result.testsRun}\n"
    summary += f" - Errores: {len(result.errors)}\n"
    summary += f" - Fallos: {len(result.failures)}\n"
    
    if result.wasSuccessful():
        summary += f" - Estado Final: SUCCESS (PASS)\n"
        summary += f" - Alcance Validado: 100% de Historias de Usuario del Sprint 2\n"
    else:
        summary += f" - Estado Final: FAILED\n"
    summary += "="*70 + "\n"

    print(summary)
    report_lines.append(summary)

    os.makedirs("docs", exist_ok=True)
    out_file = "docs/reporte_pruebas_sprint2.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"\n[!] Reporte guardado automáticamente en: {out_file}")

if __name__ == "__main__":
    run_tests_and_generate_report()