# COM-001: Reclamación de facturación B2B

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente B2B reporta una factura incorrecta —descuento no aplicado, cargo duplicado, importe erróneo— se debe investigar la discrepancia, corregir la facturación y asegurar la satisfacción del cliente.

## Condición verificable

Se activa esta regla cuando un cliente B2B (marca) reporta **una o más** de las siguientes discrepancias:

1. El importe facturado no coincide con el contrato o acuerdo comercial vigente
2. Un descuento acordado (por volumen, promocional, fidelidad) no se ha aplicado
3. Aparece un cargo duplicado en la misma o en sucesivas facturas
4. La base imponible o los impuestos aplicados son incorrectos
5. El período de facturación no corresponde al servicio prestado

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la reclamación con detalle de factura, cliente y discrepancia económica | Agente | Inmediato |
| 2 | Verificar el contrato y las condiciones acordadas del cliente en el sistema | Account manager | < 2h |
| 3 | Comparar la factura emitida vs lo que debió facturarse según contrato | Account manager | < 4h |
| 4 | Si hay error: coordinar con **Tecnología** o administración la emisión de factura rectificativa | Account manager | < 24h |
| 5 | Comunicar al cliente la corrección y nueva fecha de factura | Account manager | < 24h |
| 6 | Si no hay error: explicar al cliente el detalle de la factura y justificar cada cargo | Account manager | < 24h |
| 7 | Cerrar incidencia tras confirmación de conformidad del cliente | Agente | < 1h tras confirmación |

## Excepciones

- Si la discrepancia supera los 5000€ anuales, escalar a **Dirección**
- Si el mismo cliente reporta errores de facturación >2 veces en 6 meses, escalar a **Dirección** para revisión de proceso

## Métrica asociada

- **Tiempo medio de resolución** de reclamaciones de facturación
- **Tasa de errores de facturación** (% sobre facturas emitidas)