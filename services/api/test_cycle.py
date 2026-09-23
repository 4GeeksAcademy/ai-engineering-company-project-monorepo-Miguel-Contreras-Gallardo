"""
Test funcional del ciclo completo de vida de una incidencia.
Requiere la API corriendo en http://localhost:8000
"""
import requests, json, sys

BASE = "http://localhost:8000/api/v1/incidents"
H = {"Content-Type": "application/json"}
errors = 0

def test(name, condition, detail=""):
    global errors
    if condition:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} — {detail}")
        errors += 1

# ── 1. CREAR ───────────────────────────────────────────────────────────────
print("\n🧪 TEST 1: Crear incidencia (RF-01)")
payload = {
    "title": "Rotura de stock en SKU-4903",
    "description": "SKU-4903 no encontrado en ubicación asignada. Inventario muestra 12 uds.",
    "channel": "whatsapp",
    "channel_ref": "+1234567890",
    "category": "almacen",
    "priority": "alta",
    "incident_type": "incidencia",
    "created_by": "ana.whitfield@trackflow.com"
}
r = requests.post(f"{BASE}", json=payload)
test("Status 201", r.status_code == 201, f"Esperado 201, obtenido {r.status_code}")
inc = r.json()
inc_id = inc["id"]
test("Estado 'reported'", inc["status"] == "reported", f"Obtenido {inc['status']}")
test("ID generado", len(inc_id) > 0)

# ── 2. ASIGNAR A ÁREA ──────────────────────────────────────────────────────
print("\n🧪 TEST 2: Asignar a área responsable (RF-03)")
r = requests.post(f"{BASE}/{inc_id}/assign", json={
    "assigned_area": "almacen",
    "assigned_to": "jose.luis@trackflow.com",
    "assigned_by": "ana.whitfield@trackflow.com",
    "reason": "Incidente de stock en almacén Zaragoza"
})
test("Status 200", r.status_code == 200, f"Obtenido {r.status_code}")
inc = r.json()
test("Estado 'assigned'", inc["status"] == "assigned", f"Obtenido {inc['status']}")
test("Área 'almacen'", inc["assigned_area"] == "almacen")
test("Responsable asignado", inc["assigned_to"] == "jose.luis@trackflow.com")
test("Asignado por registrado", inc["assigned_by"] == "ana.whitfield@trackflow.com")

# ── 3. INICIAR TRABAJO ──────────────────────────────────────────────────────
print("\n🧪 TEST 3: Iniciar trabajo (assigned → in_progress)")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "in_progress",
    "changed_by": "jose.luis@trackflow.com",
    "reason": "José Luis comienza la investigación"
})
test("Status 200", r.status_code == 200)
inc = r.json()
test("Estado 'in_progress'", inc["status"] == "in_progress")

# ── 4. RESOLVER ──────────────────────────────────────────────────────────────
print("\n🧪 TEST 4: Resolver (in_progress → resolved)")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "resolved",
    "changed_by": "jose.luis@trackflow.com",
    "reason": "SKU localizado en rack incorrecto",
    "resolution": "SKU-4903 encontrado en rack B-17. Reubicado en A-03. Stock verificado: 12 uds OK."
})
test("Status 200", r.status_code == 200)
inc = r.json()
test("Estado 'resolved'", inc["status"] == "resolved")
test("Resolución guardada", inc["resolution"] is not None)
test("Resuelto por", inc["resolved_by"] == "jose.luis@trackflow.com")
test("Fecha de resolución", inc["resolved_at"] is not None)
test("Resolución no vacía", len(inc["resolution"]) > 20)

# ── 5. VERIFICAR ─────────────────────────────────────────────────────────────
print("\n🧪 TEST 5: Verificar (resolved → verified)")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "verified",
    "changed_by": "ana.whitfield@trackflow.com",
    "reason": "Ana Whitfield verifica que el SKU está correcto"
})
test("Status 200", r.status_code == 200)
inc = r.json()
test("Estado 'verified'", inc["status"] == "verified")

# ── 6. CERRAR ────────────────────────────────────────────────────────────────
print("\n🧪 TEST 6: Cerrar (verified → closed)")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "closed",
    "changed_by": "ana.whitfield@trackflow.com",
    "reason": "Incidencia verificada y cerrada"
})
test("Status 200", r.status_code == 200)
inc = r.json()
test("Estado 'closed'", inc["status"] == "closed")

# ── 7. AUDIT TRAIL ─────────────────────────────────────────────────────────
print("\n🧪 TEST 7: Auditoría completa (RF-05 ⭐)")
r = requests.get(f"{BASE}/{inc_id}/audit")
test("Status 200", r.status_code == 200)
audit = r.json()
test("Mínimo 8 eventos de auditoría", len(audit) >= 8, f"Tiene {len(audit)}")
for i, e in enumerate(audit):
    print(f"    {i+1}. [{e['change_type']}] {e['field_name']}: '{e.get('old_value','')}' → '{e.get('new_value','')}' (por {e['changed_by']})")

# ── 8. ESTADÍSTICAS ─────────────────────────────────────────────────────────
print("\n🧪 TEST 8: Estadísticas")
r = requests.get(f"{BASE}/stats")
test("Status 200", r.status_code == 200)
stats = r.json()
test("Total >= 1", stats["total"] >= 1)
print(f"    {json.dumps(stats, indent=4)}")

# ── 9. TRANSICIÓN INVÁLIDA ──────────────────────────────────────────────────
print("\n🧪 TEST 9: Transición inválida rechazada")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "in_progress",
    "changed_by": "jose.luis@trackflow.com",
    "reason": "Intento inválido"
})
test("Status 422", r.status_code == 422, f"Obtenido {r.status_code}")

# ── 10. REABRIR ─────────────────────────────────────────────────────────────
print("\n🧪 TEST 10: Reabrir (closed → reopened)")
r = requests.post(f"{BASE}/{inc_id}/transition", json={
    "status": "reopened",
    "changed_by": "ana.whitfield@trackflow.com",
    "reason": "Cliente reporta que SKU-4903 sigue sin aparecer"
})
test("Status 200", r.status_code == 200)
inc = r.json()
test("Estado 'reopened'", inc["status"] == "reopened")
test("Resolución borrada al reabrir", inc["resolution"] is None)
test("Resolved_at borrado", inc["resolved_at"] is None)
test("Resolved_by borrado", inc["resolved_by"] is None)

# ── 11. CICLO COMPLETO TRAS REAPERTURA ───────────────────────────────────────
print("\n🧪 TEST 11: Ciclo completo tras reapertura")
for t in ["triaging", "assigned", "in_progress", "resolved", "verified", "closed"]:
    payload = {"status": t, "changed_by": "jose.luis@trackflow.com", "reason": f"Ciclo rápido: {t}"}
    if t == "resolved":
        payload["resolution"] = "El error era del sistema del cliente, no nuestro. Todo OK."
    r = requests.post(f"{BASE}/{inc_id}/transition", json=payload)
    test(f"  → {t}: OK (status {r.status_code})", r.status_code == 200 and r.json()["status"] == t, f"Obtenido {r.status_code} / {r.json().get('status')}")

# ── 12. LISTAR CON FILTROS ──────────────────────────────────────────────────
print("\n🧪 TEST 12: Listar incidencias con filtros")
r = requests.get(f"{BASE}?status=closed")
test("Listar por status=closed", r.status_code == 200)
data = r.json()
test("Tiene items y total", "items" in data and "total" in data)
r2 = requests.get(f"{BASE}?category=almacen&priority=alta")
test("Listar por category+priority", r2.status_code == 200)

# ── 13. LISTADO VACÍO ──────────────────────────────────────────────────────
print("\n🧪 TEST 13: Listar con filtro sin resultados")
r = requests.get(f"{BASE}?assigned_to=nadie@trackflow.com")
test("Lista vacía retorna items vacío", r.status_code == 200 and r.json()["total"] == 0)

# ── 14. NOT FOUND ──────────────────────────────────────────────────────────
print("\n🧪 TEST 14: 404 en incidencia inexistente")
r = requests.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
test("Status 404", r.status_code == 404)

# ── RESUMEN ─────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if errors == 0:
    print("🎯 TODOS LOS TESTS PASARON ✅")
else:
    print(f"❌ {errors} TEST(S) FALLARON")
    sys.exit(1)

print(f"\n📋 Resumen del ciclo de vida:")
print(f"  ID: {inc_id}")
print(f"  Creada por: ana.whitfield@trackflow.com")
print(f"  Asignada a: jose.luis@trackflow.com (almacén)")
print(f"  Estados recorridos: reported → assigned → in_progress → resolved → verified → closed → reopened → triaging → assigned → in_progress → resolved → verified → closed")
r = requests.get(f"{BASE}/{inc_id}/audit")
print(f"  Total eventos de auditoría: {len(r.json())}")