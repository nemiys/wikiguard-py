"""Tests for GET /alerts/wikis — distinct server_name values."""


async def test_includes_newly_created_wiki(client, make_alert):
    await make_alert(rule_type="zz_wikis_marker", server_name="zz-unique-wiki.wikipedia.org")
    response = await client.get("/alerts/wikis")
    assert response.status_code == 200
    assert "zz-unique-wiki.wikipedia.org" in response.json()


async def test_results_are_deduplicated(client, make_alert):
    await make_alert(rule_type="zz_wikis_dup_a", server_name="zz-dup-wiki.wikipedia.org")
    await make_alert(rule_type="zz_wikis_dup_b", server_name="zz-dup-wiki.wikipedia.org")
    response = await client.get("/alerts/wikis")
    wikis = response.json()
    assert wikis.count("zz-dup-wiki.wikipedia.org") == 1
