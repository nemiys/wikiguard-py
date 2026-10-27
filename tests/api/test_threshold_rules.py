"""CRUD tests for POST/GET/PATCH/DELETE /threshold-rules."""


async def create_rule(client, byte_threshold=500, is_active=True):
    response = await client.post(
        "/threshold-rules",
        json={"byte_threshold": byte_threshold, "is_active": is_active},
    )
    return response


async def test_create_returns_201_with_rule(client):
    response = await create_rule(client, byte_threshold=500)
    assert response.status_code == 201
    body = response.json()
    assert body["byte_threshold"] == 500
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


async def test_create_respects_explicit_is_active_false(client):
    response = await create_rule(client, byte_threshold=500, is_active=False)
    assert response.json()["is_active"] is False


async def test_create_defaults_is_active_true_when_omitted(client):
    response = await client.post("/threshold-rules", json={"byte_threshold": 500})
    assert response.status_code == 201
    assert response.json()["is_active"] is True


async def test_list_includes_newly_created_rule(client):
    before = (await client.get("/threshold-rules")).json()
    created = (await create_rule(client, byte_threshold=321)).json()
    after = (await client.get("/threshold-rules")).json()
    assert len(after) == len(before) + 1
    assert created["id"] in {rule["id"] for rule in after}


async def test_list_includes_both_newly_created_rules(client):
    before = (await client.get("/threshold-rules")).json()
    a = (await create_rule(client, byte_threshold=100)).json()
    b = (await create_rule(client, byte_threshold=200)).json()
    after = (await client.get("/threshold-rules")).json()
    assert len(after) == len(before) + 2
    assert {a["id"], b["id"]} <= {rule["id"] for rule in after}


async def test_get_by_id_returns_matching_rule(client):
    created = (await create_rule(client, byte_threshold=500)).json()
    response = await client.get(f"/threshold-rules/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_by_id_404_when_missing(client):
    response = await client.get("/threshold-rules/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found"


async def test_update_partial_field_only_changes_that_field(client):
    created = (await create_rule(client, byte_threshold=500, is_active=True)).json()
    response = await client.patch(
        f"/threshold-rules/{created['id']}", json={"byte_threshold": 900}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["byte_threshold"] == 900
    assert body["is_active"] is True


async def test_update_empty_body_changes_nothing(client):
    created = (await create_rule(client, byte_threshold=500)).json()
    response = await client.patch(f"/threshold-rules/{created['id']}", json={})
    assert response.status_code == 200
    assert response.json()["byte_threshold"] == 500


async def test_update_404_when_missing(client):
    response = await client.patch("/threshold-rules/999999", json={"byte_threshold": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found"


async def test_delete_removes_rule(client):
    created = (await create_rule(client, byte_threshold=500)).json()
    response = await client.delete(f"/threshold-rules/{created['id']}")
    assert response.status_code == 204


async def test_delete_then_get_is_404(client):
    created = (await create_rule(client, byte_threshold=500)).json()
    await client.delete(f"/threshold-rules/{created['id']}")
    response = await client.get(f"/threshold-rules/{created['id']}")
    assert response.status_code == 404


async def test_delete_404_when_missing(client):
    response = await client.delete("/threshold-rules/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found"
