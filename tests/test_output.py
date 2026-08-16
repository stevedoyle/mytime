import json

from output import render_json


def test_single_table_produces_bare_array():
    data = [{"name": "Proj1", "hours": 3.5}, {"name": "Proj2", "hours": 1.0}]

    result = json.loads(
        render_json(data, ("2026-08-01", "2026-08-01"), "summary_by_project")
    )

    assert result["data"] == data


def test_multi_table_produces_named_key_object():
    data = {
        "by_project": [{"name": "Proj1", "hours": 3.5}],
        "by_type": [{"name": "T", "hours": 2.0}],
    }

    result = json.loads(render_json(data, ("2026-08-01", "2026-08-07"), "summary"))

    assert result["data"] == data


def test_meta_contains_date_range():
    result = json.loads(render_json([], ("2026-08-01", "2026-08-07"), "entries"))

    assert result["meta"]["date_range"] == {"from": "2026-08-01", "to": "2026-08-07"}


def test_meta_contains_report_tag():
    result = json.loads(render_json([], ("2026-08-01", "2026-08-01"), "tasks"))

    assert result["meta"]["report"] == "tasks"


def test_meta_has_no_extra_fields():
    result = json.loads(render_json([], ("2026-08-01", "2026-08-01"), "notes"))

    assert set(result["meta"].keys()) == {"date_range", "report"}
    assert set(result.keys()) == {"meta", "data"}


def test_single_day_range_uses_same_date_for_from_and_to():
    result = json.loads(render_json([], ("2026-08-16", "2026-08-16"), "entries"))

    assert result["meta"]["date_range"] == {"from": "2026-08-16", "to": "2026-08-16"}


def test_output_is_compact_single_line():
    output = render_json([{"a": 1}], ("2026-08-01", "2026-08-01"), "csv_dump")

    assert "\n" not in output
    assert ", " not in output
    assert ": " not in output


def test_output_is_valid_json():
    output = render_json([{"a": 1}], ("2026-08-01", "2026-08-01"), "csv_dump")

    parsed = json.loads(output)
    assert parsed["data"] == [{"a": 1}]
