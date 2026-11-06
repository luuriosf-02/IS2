# Reporte de Aseguramiento de la Calidad (QA) - Sprint 4

**Proyecto:** Sistema para Casa de Cambio Digital - Global Exchange  
**Hito:** Hito 6 / Sprint 4  
**Fecha:** Octubre 2026  

---

## 1. Alcance Evaluado (Sprint 4)

1. **Confirmación de Pagos:** Integración y procesamiento de transferencias SIPAP y pasarela Stripe.
2. **Notificaciones de Tasa:** Envío automático de alertas in-app, correo electrónico y actualización mediante WebSockets por cambios de cotización.
3. **Módulo de Control de Caja:** Asignación inicial por divisa, movimientos físicos de efectivo y arqueo de caja por cajero en la sucursal.

---

## 2. Resumen de Pruebas Unitarias (PUN)

| Módulo | Casos de Prueba Ejecutados | Éxito | Fallos | Cobertura |
| :--- | :---: | :---: | :---: | :---: |
| `apps.payments` | 8 | 8 | 0 | 92% |
| `apps.notifications` | 6 | 6 | 0 | 88% |
| `apps.cash_control` | 10 | 10 | 0 | 95% |
| **Total** | **24** | **24** | **0** | **91.6%** |

---

## 3. Verificación de Criterios No Funcionales

* **RNF03 (Auditabilidad):** Cada confirmación o rechazo de pago registra correctamente el `AuditLog` con ID de usuario, IP, timestamp y valores procesados.
* **RNF09 (Integridad de Caja):** Se comprobó que el modelo `CashMovement` bloquea cualquier intento de eliminación física (*hard delete*).

---

## 4. Conclusión

El software desarrollado para el Sprint 4 cumple con los criterios de aceptación y estándares de calidad definidos en el Plan de Pruebas. El alcance queda validado satisfactoriamente para la entrega formal con el TAG de release `v4.0.0-sprint4`.