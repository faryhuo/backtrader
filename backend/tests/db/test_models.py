import json

from src.db.models import SafeJSON


def test_safejson_bind_and_result_round_trip():
    t = SafeJSON()
    payload = {"a": 1, "b": ["x", "y"]}

    stored = t.process_bind_param(payload, dialect=None)
    assert isinstance(stored, str)
    assert json.loads(stored) == payload

    loaded = t.process_result_value(stored, dialect=None)
    assert loaded == payload


def test_safejson_handles_null_and_empty():
    t = SafeJSON()
    assert t.process_result_value(None, dialect=None) is None
    assert t.process_result_value("", dialect=None) is None


def test_safejson_handles_invalid_json():
    t = SafeJSON()
    assert t.process_result_value("{not-json", dialect=None) is None

