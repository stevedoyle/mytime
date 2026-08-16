---
status: accepted
date: 2026-08-16
---

# Hand-edited markdown files are the system of record, not a database

Both tools treat a directory of `YYYY-MM-DD.md` markdown files as their entire data store — there is no database, index, or import step. Files are written and edited by hand as part of a personal daily-notes workflow that predates this tool (see git history: `mytime` was extracted from an existing notes repo), and both CLIs are read-only passes over that text except for `myday --fix`, which edits a note in place. This keeps the notes portable, diffable, greppable, and editable in any editor, at the cost of no query capability beyond "regex over files in a date range" and no validation until a tool is run.

This is foundational, not incidental: a future contributor who reaches for SQLite, a JSON index, or a file-watcher/import pipeline to speed up repeated summarization would be working against the deliberate design, not fixing an oversight.
