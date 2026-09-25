# Plan tecnico: gestor de inventario de TrackFlow

## Contexto y limite

Este plan implementa [spec.md](spec.md) como servicio backend de inventario. Actualmente no hay codigo fuente versionado del servicio en `services/api`; las carpetas locales y la base de datos de desarrollo no constituyen un contrato de implementacion. El alta de articulos, almacenes y lotes debe existir antes de registrar movimientos, pero su interfaz de administracion queda fuera de esta fase. No se incluye ingesta de pedidos, alertas ni sincronizacion con los SGA.

## Persistencia

Usar PostgreSQL como fuente de verdad: sus transacciones y bloqueos de filas permiten garantizar salidas concurrentes sin saldo negativo. No usar la base de datos local SQLite como prueba de esa garantia. Tablas propuestas:

| Tabla | Claves y restricciones | Uso |
| --- | --- | --- |
| `articles` | `sku` clave primaria | Identidad del articulo. |
| `warehouses` | `id` clave primaria | Catalogo de almacenes; Los Angeles y Zaragoza se cargan como datos iniciales, no se codifican en la logica. |
| `lots` | `id` clave primaria, `sku` referencia a `articles`, `UNIQUE (sku, code)` | Un mismo codigo de lote puede pertenecer a distintos articulos; la identidad interna evita confundirlos. |
| `movements` | `id` clave primaria, `sequence` secuencia unica creciente, `request_key` unico, referencias a `lots` y `warehouses`, `type` restringido a entrada/salida, `quantity` entero `> 0`, `recorded_at` | Diario de movimientos confirmados; guardar tambien el SKU asociado al lote o resolverlo mediante la relacion, pero no almacenar una columna de stock editable. |

Los movimientos son solo de insercion: la aplicacion no expone operaciones de actualizacion o borrado y el rol de base de datos que usa para registrar movimientos no debe tener permisos `UPDATE`/`DELETE` sobre `movements`. Las correcciones son nuevos movimientos sujetos a las mismas reglas de saldo. La clave de solicitud es globalmente unica; una restriccion `UNIQUE` la protege incluso si llegan reintentos simultaneos a distintos procesos. Usar enteros para unidades evita saldos fraccionarios por redondeo.

## Lectura del stock

Una unica consulta SQL agrega movimientos por `(sku, warehouse_id, lot_id)` usando `SUM(CASE WHEN type = 'entrada' THEN quantity ELSE -quantity END)` y `COALESCE(..., 0)`. Partir de los lotes registrados y los almacenes filtrados con `LEFT JOIN` a los movimientos permite distinguir un lote existente sin historial (cero) de un lote desconocido (error). Validar primero SKU, almacen y lote solicitados, y exigir almacen cuando se indique lote. El total se suma a partir de las filas de detalle obtenidas en la misma lectura, no mediante otra consulta con otra instantanea. Sin filtro de almacen se agregan los dos almacenes sin compensar saldos entre ellos.

Las consultas usan la instantanea de una sola sentencia de PostgreSQL (`READ COMMITTED`): ven todos los commits anteriores al inicio de esa sentencia, nunca inserciones sin confirmar. Se calcula a partir del diario en esta fase, sin cache ni tabla de saldo materializado; asi solo existe una fuente de verdad y los rechazos no requieren compensar proyecciones. Si el volumen hace lenta la agregacion, anadir un indice sobre `(lot_id, warehouse_id, sequence)` y medir antes de plantear una proyeccion derivada reconstruible.

## Escritura y concurrencia

La logica vive en un servicio de dominio de inventario bajo `services/api/app/services`, invocado por la capa de entrada bajo `routers` y `schemas`; el acceso transaccional y las consultas agregadas viven bajo `db`. El router valida formato y traduce errores de dominio; nunca calcula ni escribe saldos. Toda entrada, salida o rectificacion pasa por el mismo servicio, incluidos futuros consumidores de los SGA.

1. Iniciar transaccion; validar SKU, almacen, lote y cantidad. Buscar primero la `request_key` para devolver un reintento identico o conflicto ante datos diferentes.
2. Bloquear la fila del lote (`SELECT ... FOR UPDATE`) antes de calcular el saldo. El lote existe aun con saldo cero, asi que proporciona un punto de bloqueo estable para las primeras salidas. Todas las escrituras para ese lote, en cualquier almacen, pasan por este bloqueo; esto simplifica la exclusion mutua a costa de serializar tambien almacenes distintos del mismo lote.
3. Calcular dentro de la transaccion el saldo del lote en el almacen solicitado a partir de movimientos confirmados. Si la salida lo supera, devolver stock insuficiente con saldo y cantidad sin insertar nada. Si es valida, insertar un movimiento con la clave unica y confirmar la transaccion; devolver el saldo resultante calculado tras aplicar la cantidad.
4. Si la insercion colisiona en `request_key`, deshacer la transaccion, recuperar el movimiento original confirmado y comparar todos los datos de la solicitud: iguales implican replay, diferentes implican conflicto. Para replay, reconstruir el saldo original sumando solo movimientos de ese lote y almacen hasta la `sequence` del movimiento original; no devolver el saldo actual como si fuera el resultado inicial.

El bloqueo previo al calculo evita que dos salidas del mismo lote lean a la vez un saldo que solo alcanza para una. La `sequence` permite reconstruir el resultado original: las inserciones del mismo lote se serializan bajo su bloqueo antes de recibir numero de secuencia. Tanto el control de concurrencia como la idempotencia deben ejecutarse en PostgreSQL, no depender de un bloqueo local al proceso de la API.

## Verificacion prevista

- Para INV-001, INV-002, INV-003 e INV-010: entradas, salidas y rectificaciones cambian exclusivamente el agregado del diario; una lectura posterior al commit obtiene el saldo esperado.
- Para INV-004 e INV-005: dos salidas concurrentes que superan juntas el saldo confirman como maximo una; saldo insuficiente o SKU/lote inexistente no crean movimientos.
- Para INV-006, INV-007 e INV-008: consultar ambos almacenes, lote registrado sin movimientos, identificadores desconocidos y datos invalidos distingue cero de error sin modificar datos.
- Para INV-009: repetir la misma clave con datos iguales, con datos distintos y desde dos procesos concurrentes produce un solo movimiento y el resultado original o conflicto segun corresponda.