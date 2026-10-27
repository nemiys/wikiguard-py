"""Tests for GET /alerts — sorting, filtering, severity bands, pagination.

fired_alerts is a live table: the real consumer keeps inserting rows while
these tests run. Every test that needs an exact, deterministic set of rows
creates them with a unique `rule_type` marker (e.g. "zz_sort") that real
alerts never use, and then filters the request by that same rule_type —
the API's filters are ANDed together, so this fully isolates test rows
from concurrent production noise without needing an empty table.
"""

from datetime import UTC, datetime, timedelta


def ago(minutes):
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=minutes)


# ---- sort (5 columns) ----------------------------------------------------


async def test_default_sort_is_fired_at_desc(client, make_alert):
    older = await make_alert(rule_type="zz_sort_default", fired_at=ago(10))
    newer = await make_alert(rule_type="zz_sort_default", fired_at=ago(1))
    response = await client.get("/alerts", params={"rule_type": "zz_sort_default"})
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [newer.id, older.id]


async def test_sort_fired_at_asc(client, make_alert):
    older = await make_alert(rule_type="zz_sort_fired_asc", fired_at=ago(10))
    newer = await make_alert(rule_type="zz_sort_fired_asc", fired_at=ago(1))
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sort_fired_asc", "sort": "fired_at", "order": "asc"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [older.id, newer.id]


async def test_sort_byte_change_asc(client, make_alert):
    small = await make_alert(rule_type="zz_sort_byte", byte_change=100)
    big = await make_alert(rule_type="zz_sort_byte", byte_change=9000)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sort_byte", "sort": "byte_change", "order": "asc"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [small.id, big.id]


async def test_sort_byte_change_desc(client, make_alert):
    small = await make_alert(rule_type="zz_sort_byte_desc", byte_change=100)
    big = await make_alert(rule_type="zz_sort_byte_desc", byte_change=9000)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sort_byte_desc", "sort": "byte_change", "order": "desc"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [big.id, small.id]


async def test_sort_rule_type_asc(client, make_alert):
    a = await make_alert(rule_type="zz_sort_rt_a", server_name="zz-sort-rt.wikipedia.org")
    b = await make_alert(rule_type="zz_sort_rt_b", server_name="zz-sort-rt.wikipedia.org")
    response = await client.get(
        "/alerts",
        params={"wiki": "zz-sort-rt.wikipedia.org", "sort": "rule_type", "order": "asc"},
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [a.id, b.id]


async def test_sort_wiki_asc(client, make_alert):
    a = await make_alert(rule_type="zz_sort_wiki", server_name="aa.wikipedia.org")
    b = await make_alert(rule_type="zz_sort_wiki", server_name="zz.wikipedia.org")
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sort_wiki", "sort": "wiki", "order": "asc"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [a.id, b.id]


async def test_sort_user_asc(client, make_alert):
    a = await make_alert(rule_type="zz_sort_user", user="Aaron")
    b = await make_alert(rule_type="zz_sort_user", user="Zoe")
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sort_user", "sort": "user", "order": "asc"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [a.id, b.id]


async def test_invalid_sort_column_rejected(client):
    response = await client.get("/alerts", params={"sort": "not_a_real_column"})
    assert response.status_code == 422


async def test_invalid_order_value_rejected(client):
    response = await client.get("/alerts", params={"order": "sideways"})
    assert response.status_code == 422


# ---- filtering: rule_type / wiki -----------------------------------------


async def test_filter_rule_type_returns_only_matching(client, make_alert):
    match = await make_alert(rule_type="zz_filter_rt_match")
    await make_alert(rule_type="zz_filter_rt_other")
    response = await client.get("/alerts", params={"rule_type": "zz_filter_rt_match"})
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [match.id]


async def test_filter_rule_type_excludes_nonmatching(client, make_alert):
    other = await make_alert(rule_type="zz_filter_rt_excl_other")
    response = await client.get("/alerts", params={"rule_type": "zz_filter_rt_excl_wanted"})
    ids = [item["id"] for item in response.json()["items"]]
    assert other.id not in ids


async def test_filter_wiki_returns_only_matching(client, make_alert):
    match = await make_alert(rule_type="zz_filter_wiki", server_name="match.wikipedia.org")
    await make_alert(rule_type="zz_filter_wiki", server_name="other.wikipedia.org")
    response = await client.get(
        "/alerts", params={"rule_type": "zz_filter_wiki", "wiki": "match.wikipedia.org"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [match.id]


async def test_filter_wiki_excludes_nonmatching(client, make_alert):
    other = await make_alert(rule_type="zz_filter_wiki_excl", server_name="other.wikipedia.org")
    response = await client.get(
        "/alerts", params={"rule_type": "zz_filter_wiki_excl", "wiki": "match.wikipedia.org"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert other.id not in ids


async def test_filter_no_filters_includes_newly_created_alert(client, make_alert):
    before = (await client.get("/alerts", params={"limit": 1})).json()["total"]
    await make_alert(rule_type="zz_no_filter")
    after = (await client.get("/alerts", params={"limit": 1})).json()["total"]
    assert after == before + 1


# ---- severity boundaries --------------------------------------------------


async def test_severity_high_includes_abs_at_or_above_5000(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_high", byte_change=5000)
    response = await client.get("/alerts", params={"rule_type": "zz_sev_high", "severity": "high"})
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [alert.id]


async def test_severity_high_excludes_4999(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_high_excl", byte_change=4999)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sev_high_excl", "severity": "high"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert alert.id not in ids


async def test_severity_medium_includes_500_to_4999(client, make_alert):
    low_edge = await make_alert(rule_type="zz_sev_med", byte_change=500)
    high_edge = await make_alert(rule_type="zz_sev_med", byte_change=4999)
    response = await client.get("/alerts", params={"rule_type": "zz_sev_med", "severity": "medium"})
    ids = [item["id"] for item in response.json()["items"]]
    assert {low_edge.id, high_edge.id} == set(ids)


async def test_severity_medium_excludes_499(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_med_excl_low", byte_change=499)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sev_med_excl_low", "severity": "medium"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert alert.id not in ids


async def test_severity_medium_excludes_5000(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_med_excl_high", byte_change=5000)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sev_med_excl_high", "severity": "medium"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert alert.id not in ids


async def test_severity_low_includes_below_500(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_low", byte_change=499)
    response = await client.get("/alerts", params={"rule_type": "zz_sev_low", "severity": "low"})
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [alert.id]


async def test_severity_uses_absolute_value_of_negative_byte_change(client, make_alert):
    alert = await make_alert(rule_type="zz_sev_negative", byte_change=-9000)
    response = await client.get(
        "/alerts", params={"rule_type": "zz_sev_negative", "severity": "high"}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [alert.id]


# ---- since_minutes ---------------------------------------------------------


async def test_since_minutes_includes_recent(client, make_alert):
    recent = await make_alert(rule_type="zz_since_recent", fired_at=ago(1))
    response = await client.get(
        "/alerts", params={"rule_type": "zz_since_recent", "since_minutes": 5}
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [recent.id]


async def test_since_minutes_excludes_old(client, make_alert):
    old = await make_alert(rule_type="zz_since_old", fired_at=ago(120))
    response = await client.get("/alerts", params={"rule_type": "zz_since_old", "since_minutes": 5})
    ids = [item["id"] for item in response.json()["items"]]
    assert old.id not in ids


async def test_no_since_minutes_includes_alerts_of_any_age(client, make_alert):
    old = await make_alert(rule_type="zz_no_since", fired_at=ago(120))
    response = await client.get("/alerts", params={"rule_type": "zz_no_since"})
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [old.id]


# ---- pagination -------------------------------------------------------------


async def test_pagination_limit_restricts_count(client, make_alert):
    for _ in range(5):
        await make_alert(rule_type="zz_page_limit")
    response = await client.get("/alerts", params={"rule_type": "zz_page_limit", "limit": 2})
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5


async def test_pagination_offset_skips_items(client, make_alert):
    rows = [await make_alert(rule_type="zz_page_offset", fired_at=ago(i)) for i in range(5, 0, -1)]
    response = await client.get(
        "/alerts",
        params={
            "rule_type": "zz_page_offset",
            "sort": "fired_at",
            "order": "asc",
            "limit": 2,
            "offset": 2,
        },
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [rows[2].id, rows[3].id]


async def test_pagination_total_reflects_full_count_not_just_page(client, make_alert):
    for _ in range(3):
        await make_alert(rule_type="zz_page_total")
    response = await client.get("/alerts", params={"rule_type": "zz_page_total", "limit": 1})
    assert response.json()["total"] == 3


async def test_pagination_limit_exceeding_max_rejected(client):
    response = await client.get("/alerts", params={"limit": 201})
    assert response.status_code == 422


async def test_pagination_default_limit_is_50(client, make_alert):
    for _ in range(3):
        await make_alert(rule_type="zz_page_default")
    response = await client.get("/alerts", params={"rule_type": "zz_page_default"})
    assert len(response.json()["items"]) == 3


# ---- combinations ------------------------------------------------------------


async def test_combination_filter_and_sort(client, make_alert):
    small = await make_alert(
        rule_type="zz_combo_sort", server_name="combo.wikipedia.org", byte_change=10
    )
    big = await make_alert(
        rule_type="zz_combo_sort", server_name="combo.wikipedia.org", byte_change=9999
    )
    await make_alert(rule_type="zz_combo_sort", server_name="other.wikipedia.org", byte_change=5000)
    response = await client.get(
        "/alerts",
        params={
            "rule_type": "zz_combo_sort",
            "wiki": "combo.wikipedia.org",
            "sort": "byte_change",
            "order": "desc",
        },
    )
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [big.id, small.id]


async def test_combination_filter_and_pagination(client, make_alert):
    for _ in range(4):
        await make_alert(rule_type="zz_combo_page", server_name="combo2.wikipedia.org")
    await make_alert(rule_type="zz_combo_page", server_name="other2.wikipedia.org")
    response = await client.get(
        "/alerts",
        params={"rule_type": "zz_combo_page", "wiki": "combo2.wikipedia.org", "limit": 2},
    )
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 4
