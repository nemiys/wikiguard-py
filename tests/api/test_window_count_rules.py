"""CRUD tests for POST/GET/PATCH/DELETE /window-count-rules."""


async def create_rule(client, window_seconds=60, edit_count_threshold=5, is_active=True):
    response = await client.post(
        "/window-count-rules",
        json={
            "window_seconds": window_seconds,
            "edit_count_threshold": edit_count_threshold,
            "is_active": is_active,
        },
    )
    return response


async def test_create_returns_201_with_rule(client):
    response = await create_rule(client, window_seconds=60, edit_count_threshold=5)
    assert response.status_code == 201
    body = response.json()
    assert body["window_seconds"] == 60
    assert body["edit_count_threshold"] == 5
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


async def test_create_respects_explicit_is_active_false(client):
    response = await create_rule(client, is_active=False)
    assert response.json()["is_active"] is False


async def test_create_defaults_is_active_true_when_omitted(client):
    response = await client.post(
        "/window-count-rules", json={"window_seconds": 60, "edit_count_threshold": 5}
    )
    assert response.status_code == 201
    assert response.json()["is_active"] is True


async def test_list_includes_newly_created_rule(client):
    before = (await client.get("/window-count-rules")).json()
    created = (await create_rule(client)).json()
    after = (await client.get("/window-count-rules")).json()
    assert len(after) == len(before) + 1
    assert created["id"] in {rule["id"] for rule in after}


async def test_list_includes_both_newly_created_rules(client):
    before = (await client.get("/window-count-rules")).json()
    a = (await create_rule(client, window_seconds=30, edit_count_threshold=3)).json()
    b = (await create_rule(client, window_seconds=120, edit_count_threshold=10)).json()
    after = (await client.get("/window-count-rules")).json()
    assert len(after) == len(before) + 2
    assert {a["id"], b["id"]} <= {rule["id"] for rule in after}


async def test_get_by_id_returns_matching_rule(client):
    created = (await create_rule(client)).json()
    response = await client.get(f"/window-count-rules/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_by_id_404_when_missing(client):
    response = await client.get("/window-count-rules/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Window-count rule not found"


async def test_update_single_field_only_changes_that_field(client):
    created = (await create_rule(client, window_seconds=60, edit_count_threshold=5)).json()
    response = await client.patch(
        f"/window-count-rules/{created['id']}", json={"edit_count_threshold": 9}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["edit_count_threshold"] == 9
    assert body["window_seconds"] == 60


async def test_update_other_field_only_changes_that_field(client):
    created = (await create_rule(client, window_seconds=60, edit_count_threshold=5)).json()
    response = await client.patch(
        f"/window-count-rules/{created['id']}", json={"window_seconds": 300}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["window_seconds"] == 300
    assert body["edit_count_threshold"] == 5


async def test_update_empty_body_changes_nothing(client):
    created = (await create_rule(client, window_seconds=60, edit_count_threshold=5)).json()
    response = await client.patch(f"/window-count-rules/{created['id']}", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["window_seconds"] == 60
    assert body["edit_count_threshold"] == 5


async def test_update_404_when_missing(client):
    response = await client.patch(
        "/window-count-rules/999999", json={"edit_count_threshold": 1}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Window-count rule not found"


async def test_delete_removes_rule(client):
    created = (await create_rule(client)).json()
    response = await client.delete(f"/window-count-rules/{created['id']}")
    assert response.status_code == 204


async def test_delete_then_get_is_404(client):
    created = (await create_rule(client)).json()
    await client.delete(f"/window-count-rules/{created['id']}")
    response = await client.get(f"/window-count-rules/{created['id']}")
    assert response.status_code == 404


async def test_delete_404_when_missing(client):
    response = await client.delete("/window-count-rules/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Window-count rule not found"
