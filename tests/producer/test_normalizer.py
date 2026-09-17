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


def test_missing_user_defaults_to_unknown(make_raw_change):
    raw = make_raw_change()
    del raw["user"]
    event = normalize_recentchange(raw)
    assert event.user == "unknown"


def test_negative_byte_change_for_deletion(make_raw_change):
    raw = make_raw_change(length={"old": 600, "new": 100})
    event = normalize_recentchange(raw)
    assert event.byte_change == -500
