# Tareas: gestor de inventario de TrackFlow

Cada tarea tiene un criterio principal de [spec.md](spec.md) y una comprobacion independiente. Seguir las decisiones de [plan.md](plan.md). Ejecutar las verificaciones de concurrencia contra PostgreSQL: SQLite no reproduce los bloqueos de filas previstos. Los archivos locales existentes en `services/api` no forman parte de estas tareas hasta que se decida incorporarlos expresamente.

## Persistencia

- [ ] **T01 [INV-005]** Crear la migracion de `articles`, `warehouses` y `lots`, con la asociacion obligatoria lote-articulo y catalogo inicial de Los Angeles y Zaragoza. **Verificar:** la migracion aplica en una base vacia, permite dos lotes con el mismo codigo en articulos distintos y rechaza un lote cuyo articulo no existe.
- [ ] **T02 [INV-002]** Crear la migracion del diario `movements` con identificador, secuencia, clave de solicitud unica, referencias al lote y almacen, tipo, cantidad entera positiva y fecha. **Verificar:** se inserta un movimiento valido y la base rechaza cantidad no positiva, tipo invalido, referencia inexistente y clave repetida.
- [ ] **T03 [INV-001]** Restringir el rol de escritura de la API a `INSERT`/`SELECT` sobre `movements`, sin `UPDATE` ni `DELETE`, y no exponer escritura de saldo. **Verificar:** ese rol puede insertar un movimiento pero recibe denegacion al intentar modificarlo, borrarlo o editar una columna de saldo (que no debe existir).
- [ ] **T04 [INV-001]** Implementar la consulta SQL de saldo por lote y almacen como suma de entradas menos salidas del diario confirmado. **Verificar:** para un mismo lote con dos entradas y una salida la consulta devuelve exactamente la diferencia, sin leer una tabla de saldo editable.

## Registro de movimientos

- [ ] **T05 [INV-008]** Validar en la capa de entrada tipo, cantidad entera positiva y almacen existente antes de registrar movimientos. **Verificar:** cada dato invalido produce un error de validacion y deja el numero de movimientos igual.
- [ ] **T06 [INV-002]** Implementar el registro transaccional de entradas para articulo, lote y almacen registrados. **Verificar:** una entrada valida confirma un solo movimiento y devuelve el saldo aumentado en la cantidad indicada.
- [ ] **T07 [INV-003]** Implementar la salida usando el saldo del lote y almacen dentro de la misma transaccion. **Verificar:** con saldo suficiente, una salida confirma un solo movimiento y devuelve el saldo disminuido exactamente en su cantidad.
- [ ] **T08 [INV-004]** Rechazar una salida que supere el saldo del lote y almacen con error de stock insuficiente. **Verificar:** el error incluye saldo disponible y cantidad solicitada, y no se inserta movimiento ni cambia el saldo.
- [ ] **T09 [INV-004]** Serializar las escrituras de un lote mediante bloqueo de fila en PostgreSQL antes de comprobar el saldo. **Verificar:** dos salidas simultaneas que juntas superan el saldo producen como maximo un movimiento confirmado y nunca saldo negativo.
- [ ] **T10 [INV-005]** Rechazar salidas de SKU o lote inexistente y de lote asociado a otro SKU, sin altas implicitas. **Verificar:** cada caso devuelve error de inexistencia o asociacion invalida, respectivamente, y deja sin cambios catalogos, diario y saldo.

## Consulta e idempotencia

- [ ] **T11 [INV-006]** Exponer la consulta de stock por SKU con filtros opcionales de almacen y lote, y total obtenido de las mismas filas de detalle. **Verificar:** con movimientos en ambos almacenes se obtienen los saldos separados y su suma correcta; un filtro restringe solo las filas pertinentes y se rechaza un filtro de lote sin almacen.
- [ ] **T12 [INV-007]** Distinguir recursos desconocidos de lotes registrados sin movimientos en la consulta de stock. **Verificar:** SKU, almacen o lote inexistente da error; un lote existente sin historial aparece con cero.
- [ ] **T13 [INV-009]** Detectar reintentos con la misma clave y los mismos datos, incluso entre procesos, y reconstruir el resultado original. **Verificar:** dos solicitudes identicas crean un solo movimiento y devuelven el mismo saldo resultante original aunque exista un movimiento posterior.
- [ ] **T14 [INV-009]** Rechazar la reutilizacion de una clave de solicitud con datos diferentes. **Verificar:** tras una solicitud confirmada, otra con igual clave y distinto contenido devuelve conflicto y no crea movimiento, incluso si llegan casi a la vez.
- [ ] **T15 [INV-010]** Asegurar que la lectura de stock usa una unica instantanea de movimientos confirmados. **Verificar:** una consulta posterior a un commit incluye el movimiento, mientras otra anterior al commit no incluye el movimiento pendiente ni uno rechazado.

## Catalogo y backoffice

- [x] **T16 [INV-011]** Exponer alta, listado, edicion y baja logica de articulos sin eliminar el diario. **Verificar:** las operaciones actualizan el catalogo y una baja conserva lotes y movimientos.
- [x] **T17 [INV-002]** Registrar entrada, salida y ajuste con cantidad positiva, motivo obligatorio y fecha; exigir direccion en los ajustes. **Verificar:** un ajuste de aumento suma, uno de reduccion resta y no puede dejar saldo negativo.
- [x] **T18 [INV-012]** Mostrar en el backoffice el punto de reorden y una senal visible cuando el stock derivado quede por debajo. **Verificar:** la tabla y el contador cambian al cruzar el umbral sin editar el saldo directamente.