from app.services.response_cache import clear, get_or_set, invalidate


def test_get_or_set_reuses_value_until_ttl_expires():
    clear()
    calls = []

    def loader():
        calls.append("called")
        return {"count": len(calls)}

    assert get_or_set("stats:one", loader, ttl_seconds=60) == {"count": 1}
    assert get_or_set("stats:one", loader, ttl_seconds=60) == {"count": 1}
    assert calls == ["called"]


def test_cached_values_are_copied_and_prefix_invalidation_is_scoped():
    clear()
    get_or_set("inventory:reorder:db1", lambda: {"items": ["SKU-1"]})
    get_or_set("inventory:reorder:db2", lambda: {"items": ["SKU-2"]})

    modified = get_or_set("inventory:reorder:db1", lambda: {})
    modified["items"].append("MUTATED")
    assert get_or_set("inventory:reorder:db1", lambda: {}) == {"items": ["SKU-1"]}

    invalidate("inventory:reorder:db1")
    assert get_or_set("inventory:reorder:db2", lambda: {}) == {"items": ["SKU-2"]}
    assert get_or_set("inventory:reorder:db1", lambda: {"items": ["FRESH"]}) == {"items": ["FRESH"]}


def test_cache_does_not_hold_lock_while_loading():
    clear()
    calls = []

    def loader():
        calls.append(True)
        return [1, 2]

    assert get_or_set("test:loader", loader) == [1, 2]
    assert get_or_set("test:loader", loader) == [1, 2]
    assert len(calls) == 1
