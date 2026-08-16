"""Shared JSON serialization for mytime and myday report output."""

import json


def render_json(data, date_range, report):
    """Serialize a report's rows into the compact `{meta, data}` JSON envelope.

    `data` is either a list[dict] (single-table report, serialized as a bare
    array) or a dict[str, list[dict]] (multi-table report, serialized with
    the same named keys). `date_range` is a (start, end) tuple of ISO
    YYYY-MM-DD date strings. `report` is a string tag identifying the report
    shape.
    """
    start, end = date_range
    envelope = {
        "meta": {
            "date_range": {"from": start, "to": end},
            "report": report,
        },
        "data": data,
    }
    return json.dumps(envelope, separators=(",", ":"))
