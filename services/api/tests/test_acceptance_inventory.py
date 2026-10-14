from pathlib import Path

from app.db.models import Article, Lot, Movement


def movement_count(inventory_env):
    with inventory_env.session_factory() as session:
        return session.query(Movement).count()


def test_inv_001_and_invariant_1_stock_is_derived_and_has_no_write_endpoint(
    inventory_env, movement_payload
):
    assert "stock" not in Article.__table__.columns
    assert "stock" not in Movement.__table__.columns
    assert inventory_env.client.put("/inventory/movements", json={}).status_code == 405
    assert inventory_env.client.delete("/inventory/movements").status_code == 405

    response = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=7)
    )
    assert response.status_code == 201
    assert response.json()["resulting_stock"] == 7


def test_inv_002_valid_entry_creates_one_movement_and_increases_stock(
    inventory_env, movement_payload
):
    response = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=8)
    )

    assert response.status_code == 201
    assert response.json()["resulting_stock"] == 8
    assert movement_count(inventory_env) == 1


def test_inv_003_valid_output_creates_one_movement_and_decreases_stock(
    inventory_env, movement_payload
):
    inventory_env.client.post("/inventory/movements", json=movement_payload(quantity=10))
    response = inventory_env.client.post(
        "/inventory/movements",
        json=movement_payload(
            type="salida", quantity=4, request_key="request-output"
        ),
    )

    assert response.status_code == 201
    assert response.json()["resulting_stock"] == 6
    assert movement_count(inventory_env) == 2


def test_inv_004_and_invariant_2_insufficient_stock_is_rejected_without_changes(
    inventory_env, movement_payload
):
    inventory_env.client.post("/inventory/movements", json=movement_payload(quantity=2))
    response = inventory_env.client.post(
        "/inventory/movements",
        json=movement_payload(
            type="salida", quantity=3, request_key="request-output"
        ),
    )

    assert response.status_code == 422
    assert "available=2" in response.json()["detail"]
    assert "requested=3" in response.json()["detail"]
    assert movement_count(inventory_env) == 1
    assert inventory_env.client.get("/inventory/stock?sku=SKU-1").json()["total"] == 2


def test_inv_005_unknown_or_mismatched_resources_do_not_create_catalog_data(
    inventory_env, movement_payload
):
    with inventory_env.session_factory() as session:
        session.add(Article(sku="SKU-2", name="Gateway", reorder_point=2))
        session.flush()
        session.add(Lot(sku="SKU-2", code="LOT-OTHER"))
        session.commit()

    responses = [
        inventory_env.client.post(
            "/inventory/movements",
            json=movement_payload(sku="UNKNOWN", request_key="unknown-sku"),
        ),
        inventory_env.client.post(
            "/inventory/movements",
            json=movement_payload(lot_code="UNKNOWN", request_key="unknown-lot"),
        ),
        inventory_env.client.post(
            "/inventory/movements",
            json=movement_payload(lot_code="LOT-OTHER", request_key="wrong-lot"),
        ),
    ]

    assert [response.status_code for response in responses] == [404, 404, 404]
    assert movement_count(inventory_env) == 0
    with inventory_env.session_factory() as session:
        assert session.query(Article).count() == 2
        assert session.query(Lot).count() == 2


def test_inv_006_stock_lists_warehouses_lots_filters_and_consistent_total(
    inventory_env, movement_payload
):
    assert inventory_env.client.post(
        "/articles/SKU-1/lots", json={"code": "LOT-2"}
    ).status_code == 201
    inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=4)
    )
    inventory_env.client.post(
        "/inventory/movements",
        json=movement_payload(
            warehouse_id="ZAZ", lot_code="LOT-2", quantity=6, request_key="zaz-entry"
        ),
    )

    all_stock = inventory_env.client.get("/inventory/stock?sku=SKU-1").json()
    lax_stock = inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&warehouse_id=LAX"
    ).json()
    lot_stock = inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&warehouse_id=ZAZ&lot_code=LOT-2"
    ).json()

    assert len(all_stock["lines"]) == 4
    assert all_stock["total"] == sum(line["stock"] for line in all_stock["lines"]) == 10
    assert len(lax_stock["lines"]) == 2
    assert lax_stock["total"] == 4
    assert lot_stock["total"] == 6


def test_inv_007_unknown_filters_fail_but_registered_empty_lot_is_zero(inventory_env):
    assert inventory_env.client.get("/inventory/stock?sku=UNKNOWN").status_code == 404
    assert inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&warehouse_id=UNKNOWN"
    ).status_code == 404
    assert inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&warehouse_id=LAX&lot_code=UNKNOWN"
    ).status_code == 404
    assert inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&lot_code=LOT-1"
    ).status_code == 400

    response = inventory_env.client.get(
        "/inventory/stock?sku=SKU-1&warehouse_id=LAX&lot_code=LOT-1"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_inv_008_invalid_input_and_unknown_warehouse_leave_ledger_unchanged(
    inventory_env, movement_payload
):
    responses = [
        inventory_env.client.post(
            "/inventory/movements", json=movement_payload(quantity=0, request_key="zero")
        ),
        inventory_env.client.post(
            "/inventory/movements", json=movement_payload(quantity=1.5, request_key="decimal")
        ),
        inventory_env.client.post(
            "/inventory/movements", json=movement_payload(type="traslado", request_key="type")
        ),
        inventory_env.client.post(
            "/inventory/movements",
            json=movement_payload(warehouse_id="UNKNOWN", request_key="warehouse"),
        ),
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 404]
    assert movement_count(inventory_env) == 0


def test_inv_009_and_invariant_3_replay_returns_original_result_and_conflict_is_clean(
    inventory_env, movement_payload
):
    first = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=4)
    )
    inventory_env.client.post(
        "/inventory/movements",
        json=movement_payload(quantity=2, request_key="later-entry"),
    )
    replay = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=4)
    )
    conflict = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=5)
    )

    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    assert replay.json()["resulting_stock"] == 4
    assert conflict.status_code == 409
    assert movement_count(inventory_env) == 2


def test_inv_010_and_invariant_4_committed_and_rejected_movements_shape_reads(
    inventory_env, movement_payload
):
    before = inventory_env.client.get("/inventory/stock?sku=SKU-1").json()["total"]
    accepted = inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=3)
    )
    rejected = inventory_env.client.post(
        "/inventory/movements",
        json=movement_payload(type="salida", quantity=4, request_key="rejected"),
    )
    after = inventory_env.client.get("/inventory/stock?sku=SKU-1").json()["total"]

    assert before == 0
    assert accepted.status_code == 201
    assert rejected.status_code == 422
    assert after == 3


def test_inv_011_crud_and_logical_delete_preserve_history(inventory_env, movement_payload):
    created = inventory_env.client.post(
        "/articles/",
        json={
            "sku": "SKU-NEW",
            "name": "Etiqueta",
            "description": "Etiqueta térmica",
            "reorder_point": 12,
        },
    )
    listed = inventory_env.client.get("/articles/")
    updated = inventory_env.client.put(
        "/articles/SKU-NEW", json={"name": "Etiqueta 4x6", "reorder_point": 20}
    )
    inventory_env.client.post("/inventory/movements", json=movement_payload(quantity=2))
    deleted = inventory_env.client.delete("/articles/SKU-1")

    assert created.status_code == 201
    assert any(article["sku"] == "SKU-NEW" for article in listed.json())
    assert updated.json()["name"] == "Etiqueta 4x6"
    assert updated.json()["reorder_point"] == 20
    assert deleted.status_code == 204
    assert inventory_env.client.get("/articles/SKU-1").json()["active"] is False
    assert movement_count(inventory_env) == 1


def test_inv_012_reorder_signal_and_backoffice_are_visible(inventory_env, movement_payload):
    initial = inventory_env.client.get("/inventory/reorder").json()
    inventory_env.client.post(
        "/inventory/movements", json=movement_payload(quantity=6)
    )
    replenished = inventory_env.client.get("/inventory/reorder").json()

    repository_root = Path(__file__).resolve().parents[3]
    html = (repository_root / "uis/backoffice/index.html").read_text()
    javascript = (repository_root / "uis/backoffice/app.js").read_text()

    assert initial["total_below_reorder"] == 1
    assert replenished["total_below_reorder"] == 0
    assert "BAJO REORDEN" in html
    assert "/inventory/reorder" in javascript