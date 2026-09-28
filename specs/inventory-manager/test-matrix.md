# Matriz de trazabilidad de pruebas

Cada prueba incluye el criterio que verifica en su nombre. Las pruebas portables
usan la API con SQLite solo para contratos y reglas deterministas. Las garantias
de bloqueo, aislamiento, secuencia e inmutabilidad se ejecutan exclusivamente
contra PostgreSQL.

| Criterio | Tareas | Prueba principal | Entorno |
| --- | --- | --- | --- |
| INV-001 | T03, T04 | `test_inv_001_and_invariant_1_stock_is_derived_and_has_no_write_endpoint`, `test_inv_001_postgres_ledger_rejects_update_and_delete` | Portable + PostgreSQL |
| INV-002 | T02, T06, T17 | `test_inv_002_valid_entry_creates_one_movement_and_increases_stock`, `test_inv_002_postgres_identity_sequence_is_unique_and_increasing` | Portable + PostgreSQL |
| INV-003 | T07 | `test_inv_003_valid_output_creates_one_movement_and_decreases_stock` | Portable |
| INV-004 | T08, T09 | `test_inv_004_and_invariant_2_insufficient_stock_is_rejected_without_changes`, `test_inv_004_and_invariant_2_concurrent_outputs_never_make_stock_negative` | Portable + PostgreSQL |
| INV-005 | T01, T10 | `test_inv_005_unknown_or_mismatched_resources_do_not_create_catalog_data`, `test_inv_005_and_inv_008_postgres_constraints_reject_invalid_movements` | Portable + PostgreSQL |
| INV-006 | T11 | `test_inv_006_stock_lists_warehouses_lots_filters_and_consistent_total` | Portable |
| INV-007 | T12 | `test_inv_007_unknown_filters_fail_but_registered_empty_lot_is_zero` | Portable |
| INV-008 | T05 | `test_inv_008_invalid_input_and_unknown_warehouse_leave_ledger_unchanged`, `test_inv_005_and_inv_008_postgres_constraints_reject_invalid_movements` | Portable + PostgreSQL |
| INV-009 | T13, T14 | `test_inv_009_and_invariant_3_replay_returns_original_result_and_conflict_is_clean`, `test_inv_009_concurrent_identical_replay_creates_one_movement`, `test_inv_009_concurrent_conflict_commits_one_and_rejects_one` | Portable + PostgreSQL |
| INV-010 | T15 | `test_inv_010_and_invariant_4_committed_and_rejected_movements_shape_reads`, `test_inv_010_and_invariant_4_reads_only_committed_movements` | Portable + PostgreSQL |
| INV-011 | T16 | `test_inv_011_crud_and_logical_delete_preserve_history` | Portable |
| INV-012 | T18 | `test_inv_012_reorder_signal_and_backoffice_are_visible` | Portable |

## Ejecucion

```bash
cd services/api
.venv/bin/pytest -q
```

Para incluir concurrencia y aislamiento debe proporcionarse una base PostgreSQL
dedicada. La suite crea y elimina un esquema temporal dentro de ella:

```bash
TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost/test_db \
  .venv/bin/pytest -q
```

Un resultado con pruebas PostgreSQL omitidas no verifica T03, T09, T13, T14 ni
la visibilidad transaccional de T15.
