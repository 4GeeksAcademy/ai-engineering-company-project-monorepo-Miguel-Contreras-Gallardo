# Especificacion: gestor de inventario de TrackFlow

## Alcance

El gestor unifica la consulta y el registro de inventario de los almacenes de Los Angeles y Zaragoza. Permite consultar existencias por SKU, almacen y lote, asi como el total por SKU entre almacenes. El pipeline de pedidos, las alertas y las integraciones con los SGA quedan fuera de esta especificacion; pueden consumir estos contratos sin modificar el saldo directamente.

## Modelo y contratos funcionales

- **Articulo:** SKU unico e identificador de un articulo previamente registrado.
- **Almacen:** identificador de un almacen registrado (Los Angeles o Zaragoza).
- **Lote:** identificador asociado a un articulo registrado. Cada movimiento se imputa a un lote y un almacen; no se mezclan lotes ni almacenes para autorizar una salida.
- **Movimiento:** registro inmutable con identificador unico, SKU, almacen, lote, tipo (`entrada` o `salida`), cantidad entera positiva y fecha de registro. Una entrada suma unidades; una salida resta unidades. Una rectificacion se realiza mediante un nuevo movimiento, nunca alterando uno ya registrado.
- **Registrar movimiento:** recibe SKU, almacen, lote, tipo, cantidad y una clave unica de solicitud para evitar duplicados en reintentos. Solo acepta articulos, almacenes y lotes registrados y asociados correctamente. Devuelve el movimiento confirmado y el stock resultante para ese SKU, almacen y lote. Repetir la misma clave con los mismos datos devuelve el resultado original sin registrar otro movimiento; reutilizarla con otros datos devuelve un conflicto sin cambios.
- **Consultar stock:** recibe un SKU registrado y, opcionalmente, almacen y lote (el lote exige indicar almacen). Devuelve las unidades por lote y almacen dentro del filtro, y el total del filtro. Un lote registrado sin movimientos tiene saldo cero; un SKU, almacen o lote desconocido devuelve error de recurso inexistente, no un saldo ficticio.
- **Errores de escritura:** una cantidad no positiva o no entera, un tipo invalido o un lote que no pertenece al SKU se rechazan sin cambios. Una salida sin saldo suficiente devuelve error de stock insuficiente con saldo disponible y cantidad solicitada. Una salida de articulo o lote inexistente devuelve error de recurso inexistente sin crearlos implicitamente.

## Invariantes

1. Para cada combinacion de SKU, almacen y lote, `stock = suma(entradas confirmadas) - suma(salidas confirmadas)`. El total por SKU o almacen es la suma de los saldos de sus lotes; el stock nunca se edita directamente.
2. Ningun saldo por SKU, almacen y lote puede ser negativo. La comprobacion de saldo y el registro de una salida son atomicos, incluso ante solicitudes concurrentes.
3. Un movimiento confirmado aparece una sola vez en el historial y contribuye una sola vez al saldo. Un rechazo no crea movimientos ni cambia el stock.
4. Las consultas reflejan todos los movimientos confirmados hasta el momento de la consulta y no incluyen movimientos rechazados o pendientes.

## Criterios de aceptacion (EARS)

- **INV-001 (ubicuidad):** El gestor debera derivar siempre el stock exclusivamente de los movimientos confirmados por SKU, almacen y lote; nunca debera permitir editar directamente el stock ni modificar o eliminar un movimiento confirmado.
- **INV-002 (evento):** Cuando se registre una entrada valida de cantidad positiva para un articulo, almacen y lote registrados, el gestor debera confirmar un unico movimiento y aumentar el saldo de esa combinacion en esa cantidad.
- **INV-003 (evento):** Cuando se registre una salida valida cuya cantidad no supere el saldo de su SKU, almacen y lote, el gestor debera confirmar un unico movimiento y disminuir ese saldo en esa cantidad.
- **INV-004 (comportamiento no deseado):** Si una salida dejaria negativo el saldo de su SKU, almacen y lote, el gestor debera rechazarla con error de stock insuficiente, indicar saldo disponible y cantidad solicitada, y conservar intactos historial y saldos, tambien ante salidas concurrentes.
- **INV-005 (comportamiento no deseado):** Si se intenta registrar una salida de un articulo inexistente o un lote inexistente o no asociado al articulo, el gestor debera devolver error de recurso inexistente o de asociacion invalida, respectivamente, sin crear articulo, lote ni movimiento y sin cambiar el stock.
- **INV-006 (evento):** Cuando se consulte un SKU registrado, el gestor debera devolver los saldos actuales por almacen y lote segun los filtros y un total igual a su suma, incluyendo Los Angeles y Zaragoza si no se filtra por almacen.
- **INV-007 (comportamiento no deseado):** Si se consulta un SKU, almacen o lote inexistente, el gestor debera indicar recurso inexistente en lugar de informar stock cero; un lote registrado sin movimientos debera devolver cero.
- **INV-008 (comportamiento no deseado):** Si una solicitud de movimiento tiene cantidad no entera o no positiva, tipo invalido o un almacen inexistente, el gestor debera rechazarla sin registrar movimiento ni alterar saldo alguno.
- **INV-009 (evento):** Cuando se reintente una solicitud con la misma clave y los mismos datos, el gestor debera devolver el resultado original sin duplicar el movimiento; si la clave se reutiliza con otros datos, debera devolver conflicto sin alterar el historial.
- **INV-010 (evento):** Cuando se confirme un movimiento, cualquier consulta posterior debera reflejarlo en el saldo; los movimientos pendientes o rechazados no deberan aparecer en el saldo consultado.