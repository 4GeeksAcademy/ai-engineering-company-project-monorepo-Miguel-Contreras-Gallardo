# Reglas de base de datos PostgreSQL

## Transacciones y concurrencia
- Usar `SELECT ... FOR UPDATE` para bloquear filas de lote antes de calcular saldo
- La comprobación de saldo y la inserción del movimiento deben ocurrir en **la misma transacción**
- Usar `READ COMMITTED` (default de PostgreSQL) — no cambiar el nivel de aislamiento

## Tabla movements (reglas críticas)
- **Solo INSERT** — nunca exponer UPDATE/DELETE sobre movements
- El rol de base de datos de la API solo tiene permisos INSERT y SELECT sobre movements
- Columna `request_key` con restricción UNIQUE para idempotencia
- Columna `sequence` — secuencia única creciente (SERIAL o IDENTITY)
- Cantidad siempre entera positiva (CHECK constraint)
- Tipo restringido a valores válidos: 'entrada', 'salida', 'ajuste'

## Consulta de stock
- Stock se calcula como: `SUM(CASE WHEN type = 'entrada' THEN quantity ELSE -quantity END)`
- Usar `LEFT JOIN` desde lotes para distinguir saldo cero de lote inexistente
- Una sola sentencia SQL para toda la consulta (instantánea consistente)
- Sin tabla de saldo materializado — el diario es la única fuente de verdad

## Migraciones (Alembic)
- Una migración por cambio lógico
- Las migraciones deben ser reversibles (upgrade + downgrade)
- Nombrar migraciones descriptivamente: `XXXX_add_movements_table.py`