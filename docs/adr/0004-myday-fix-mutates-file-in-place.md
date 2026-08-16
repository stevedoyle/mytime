---
status: accepted
date: 2026-08-16
---

# myday --fix rewrites the daily note in place, and only ever closes gaps

`myday --validate --fix` doesn't just report time gaps — it edits the daily note file directly, extending the end time of the block before a gap so the schedule becomes contiguous. This is a real trade-off: a tool silently rewriting a user's hand-edited source file is unusual and risky, but the alternative (report-only) leaves the daily annoyance of manually nudging end times on every gap, which is the exact friction `--fix` exists to remove for a daily journaling workflow. The scope was deliberately kept narrow to limit the blast radius: `--fix` requires `--validate` to be passed explicitly (never runs implicitly), only closes gaps, and never touches overlaps — those must always be resolved by hand, since there's no safe automatic resolution for two blocks claiming the same time.

A future change that makes `--fix` resolve overlaps automatically, or run without an explicit flag, would be reopening this decision, not extending it.
