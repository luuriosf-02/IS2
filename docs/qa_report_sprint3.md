# Reporte de Calidad de Software (QA) - Sprint 3

**Proyecto:** Global Exchange  
**Sprint:** 3 (Hito 5)  
**Fecha:** 02 de Octubre de 2026  
**Responsable:** Equipo de QA / Desarrollo  

---

## 1. Alcance Evaluado
En este sprint se validaron las historias de usuario asociadas a las transacciones de cambio de divisas:
- **Operación de compra/venta:** Cálculo automático de comisión (1.5%) y fijación de tasa aplicada.
- **Cancelación de transacción:** Bloqueo y cancelación automática por variación de cotización antes del pago.
- **Historial de transacciones:** Consulta en modo solo lectura (`GET`).

---

## 2. Resultados de Pruebas Automáticas

Las pruebas fueron ejecutadas mediante el script `ejecutor_pruebas_sprint3.py`:

| ID | Caso de Prueba | Resultado | Estado |
|---|---|---|---|
| **TC01** | Operación de compra/venta con comisión y tasa | Exitoso | PASS |
| **TC02** | Cancelación por cambio de cotización antes del pago | Exitoso | PASS |
| **TC03** | Historial de transacciones restringido a consulta | Exitoso | PASS |

- **Total de pruebas ejecutadas:** 3
- **Pruebas exitosas:** 3
- **Fallos / Errores:** 0
- **Porcentaje de cobertura de alcance:** 100%

---

## 3. Métricas de Calidad de Software

- **Bugs Críticos:** 0
- **Bugs Menores:** 0
- **Densidad de Defectos:** 0% en ambiente de pruebas
- **Estado de Build:** Estable y listo para despliegue en ambiente de producción (AMB).

---

## 4. Conclusión

El incremento de software desarrollado durante el Sprint 3 cumple con todos los criterios de aceptación y estándares de calidad requeridos para el Hito 5.