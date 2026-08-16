---
status: accepted
date: 2026-08-16
---

# JSON output uses a {meta, data} envelope; all diagnostics go to stderr, never stdout

`--format json` on both tools emits a single compact JSON object — `{"meta": {"date_range": {...}, "report": "..."}, "data": ...}` — via the shared `render_json()` in `output.py`, rather than each tool inventing its own ad-hoc schema per report type. The `report` tag exists so a consumer can dispatch on shape without guessing from the `data` payload alone, and `meta.date_range` is included because every report is implicitly scoped to a range that would otherwise be lost once the JSON leaves the process. Equally deliberate: validation errors, gap-fix diagnostics, and warnings are always written to stderr, never folded into the JSON payload or left on stdout — this is what makes `myday --format json` pipeable (`myday --format json | jq ...`) even when there are gaps to report, and it's why `myday`'s period-mode status output was moved off stdout (PR #83) after it leaked into JSON consumers' pipelines.

**Considered**: embedding warnings/errors as a field inside the JSON envelope (e.g. `data.warnings`). Rejected because it would force every consumer to parse JSON just to check for diagnostics, defeating the point of a clean stdout/stderr split for a Unix-composable tool.
