---
status: accepted
date: 2026-08-16
---

# Two separate CLI tools instead of one unified time tracker

`mytime` and `myday` both summarize personal time-tracking data, but were kept as two independent tools with independent parsers, data models, and CLIs rather than merged into a single "time" command. `mytime` answers "how did my hours split across categories over a range of days" (aggregation, no clock-time precision needed); `myday` answers "is today's schedule internally consistent" (gap/overlap validation against actual `HH:MM` ranges). These are different enough questions, over different enough data shapes, that a shared tool would need either a lowest-common-denominator format or an internal mode switch — we chose two small tools per the project's Unix-philosophy convention (see the user-level CLAUDE.md) instead.

**Considered**: a single `mytime` binary with subcommands (`mytime blocks`, `mytime categories`). Rejected because the two data models don't compose — category rollups don't need clock times, block validation doesn't need the category hierarchy — and a shared subcommand structure would couple their release cadence and flags for no shared benefit.
