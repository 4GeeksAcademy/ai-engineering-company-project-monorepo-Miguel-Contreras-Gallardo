# DIR-001: Crisis operativa global

**Ámbito:** Dirección
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando ocurre una crisis que afecta a toda la operación —caída total de sistemas que impacta ambos países, parada simultánea de almacenes, desastre natural, o cualquier evento que ponga en riesgo la continuidad del negocio— se debe activar el comité de crisis y coordinar la respuesta.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Caída total de sistemas que afecta a las operaciones de EE.UU. y España simultáneamente
2. Parada total de almacén en uno o ambos países por >2 horas
3. Un incidente de seguridad con brecha de datos de clientes confirmada (TEC-004 crítica)
4. Un evento externo (desastre natural, huelga de transportistas, pandemia) que impide la operación
5. Pérdida de datos crítica que afecta a la contabilidad o facturación

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Declarar estado de crisis y convocar al comité de crisis (CEO, CTO, responsables de departamento) | CEO / CTO | < 15 min |
| 2 | Evaluar el impacto: pedidos afectados, clientes afectados, daño económico estimado | Dirección | < 1h |
| 3 | Activar plan de contingencia: comunicación a todos los departamentos, modo manual si aplica | Dirección | < 1h |
| 4 | Designar un coordinador de crisis (único punto de comunicación) | CEO | < 30 min |
| 5 | Comunicar a los clientes afectados a través de CX y Comercial según plan de comunicación | CX / Comercial | < 2h |
| 6 | Ejecutar acciones de remediación con los departamentos implicados | Cada departamento | Según plan |
| 7 | Realizar reuniones de seguimiento cada 2h hasta resolución | Comité de crisis | Cada 2h |
| 8 | Documentar la crisis, las acciones tomadas y las lecciones aprendidas | Dirección | < 1 semana |
| 9 | Cerrar crisis solo cuando todos los sistemas estén operativos y los clientes notificados | CEO | Tras verificación |

## Excepciones

- Si hay víctimas o daños personales, contactar a servicios de emergencia antes que nada
- Si hay implicaciones legales, contactar a asesoría legal externa

## Métrica asociada

- **Tiempo de resolución de crisis**
- **Impacto económico de la crisis** (coste directo + compensaciones)