from wikiguard_py.producer.normalizer import normalize_recentchange


def test_valid_edit_is_normalized(make_raw_change):
    raw = make_raw_change()
    event = normalize_recentchange(raw)

    assert event is not None
    assert event.event_id == "hewiki:123"
    assert event.page_title == "עמוד ראשי"
    assert event.byte_change == 100


def test_non_edit_type_is_discarded(make_raw_change):
    raw = make_raw_change(type="log")
    assert normalize_recentchange(raw) is None


def test_non_content_namespace_is_discarded(make_raw_change):
    raw = make_raw_change(namespace=1)
    assert normalize_recentchange(raw) is None


def test_non_wikipedia_project_is_discarded(make_raw_change):
    raw = make_raw_change(wiki="wikidatawiki", server_name="www.wikidata.org")
    assert normalize_recentchange(raw) is None


def test_missing_user_defaults_to_unknown(make_raw_change):
    raw = make_raw_change()
    del raw["user"]
    event = normalize_recentchange(raw)
    assert event.user == "unknown"


def test_negative_byte_change_for_deletion(make_raw_change):
    raw = make_raw_change(length={"old": 600, "new": 100})
    event = normalize_recentchange(raw)
    assert event.byte_change == -500


def test_bare_wikipedia_org_without_subdomain_is_discarded(make_raw_change):
    """endswith(".wikipedia.org") requires a leading dot — "wikipedia.org"
    on its own is shorter than the suffix and correctly fails the check,
    not a false positive just because it "contains" the right words."""
    raw = make_raw_change(server_name="wikipedia.org")
    assert normalize_recentchange(raw) is None


def test_zero_byte_change_is_preserved(make_raw_change):
    raw = make_raw_change(length={"old": 500, "new": 500})
    event = normalize_recentchange(raw)
    assert event.byte_change == 0


def test_bot_flag_is_preserved(make_raw_change):
    raw = make_raw_change(bot=True)
    event = normalize_recentchange(raw)
    assert event.is_bot is True
