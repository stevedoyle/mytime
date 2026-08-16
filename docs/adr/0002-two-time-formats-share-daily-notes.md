---
status: accepted
date: 2026-08-16
---

# Two unrelated time-tracking syntaxes coexist in the same daily note file

A single `YYYY-MM-DD.md` daily note can contain both mytime's hierarchical `Time.Category.Name: hours` entries and myday's `## Time` section of `HH:MM - HH:MM Type: #ProjectCode Description` blocks — two grammars, parsed by two separate regexes, with no shared schema. This wasn't unified into one format because they capture different information: category entries are a hand-rolled hours breakdown with no notion of *when*, while time blocks are a literal schedule that can be validated for gaps and overlaps. Forcing one format to serve both would mean either computing category rollups from a full day's block schedule (losing the freedom to log rough hour estimates without an exact schedule) or adding clock-time precision to category entries that don't need it.

**Consequence**: a daily note's time-tracking sections must be read as two unrelated mini-languages, not one schema — this is the single most surprising thing about the file format to a new reader, and it's deliberate, not accidental drift.
