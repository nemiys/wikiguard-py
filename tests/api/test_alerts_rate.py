"""Tests for GET /alerts/rate — bucketed alert counts over a trailing window.

This endpoint has no filter params, so test rows can't be isolated from
concurrent production alerts the way test_alerts.py does — these tests
assert on bucket shape and relative (before/after) deltas instead of
absolute equality, same reasoning as the domain-layer stats tests.
"""

from datetime import UTC, datetime, timedelta


def ago(minutes):
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=minutes)


async def test_default_shape_is_10_buckets(client):
    response = await client.get("/alerts/rate")
    assert response.status_code == 200
    assert len(response.json()) == 10


async def test_custom_bucket_count_respected(client):
    response = await client.get("/alerts/rate", params={"buckets": 5})
    assert len(response.json()) == 5


async def test_counts_are_non_negative_integers(client):
    response = await client.get("/alerts/rate")
    assert all(isinstance(count, int) and count >= 0 for count in response.json())


async def test_recent_alert_increases_the_bucket_sum(client, make_alert):
    # Summed across all buckets, not indexed into a specific one: which
    # exact bucket our alert lands in depends on "now" at request time,
    # computed fresh on each of these two separate calls — indexing into
    # a single bucket races on that boundary. ago(0) is unambiguously
    # inside a 10-minute window either way, so the sum isn't.
    before = (await client.get("/alerts/rate", params={"minutes": 10, "buckets": 10})).json()
    await make_alert(rule_type="zz_rate_recent", fired_at=ago(0))
    after = (await client.get("/alerts/rate", params={"minutes": 10, "buckets": 10})).json()
    assert sum(after) >= sum(before) + 1


async def test_wider_window_sum_is_at_least_narrower_window_sum(client):
    # A real alert firing between these two calls can only ever grow a
    # live, unfiltered count — never shrink it — so this stays true
    # regardless of concurrent production traffic, unlike comparing
    # exact bucket arrays before/after a single insert would.
    narrow = (await client.get("/alerts/rate", params={"minutes": 5, "buckets": 5})).json()
    wide = (await client.get("/alerts/rate", params={"minutes": 60, "buckets": 5})).json()
    assert sum(wide) >= sum(narrow)


async def test_invalid_bucket_count_rejected(client):
    response = await client.get("/alerts/rate", params={"buckets": 0})
    assert response.status_code == 422


async def test_minutes_above_max_rejected(client):
    response = await client.get("/alerts/rate", params={"minutes": 1441})
    assert response.status_code == 422
