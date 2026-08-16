# mytime

A CLI toolkit for extracting and summarizing personal time-tracking data recorded by hand in daily markdown notes. Two independent tools, `mytime` and `myday`, read different sub-formats out of the same notes.

## Language

**Daily note**:
A markdown file named `YYYY-MM-DD.md` that a person edits by hand each day, containing free-form notes plus one or more recognized time-tracking sections.
_Avoid_: Log file, journal entry

**Time entry** (mytime):
A single line in a daily note of the form `Time.Category.Name: hours`, e.g. `Time.Proj.Example1: 3.5`. Reports hours spent, not a time-of-day range.
_Avoid_: Time record, time line

**Category** (mytime):
The first segment of a time entry's dotted key — one of `Proj`, `Area`, `Focus`, or `Prof`. Groups time entries for summarization; not user-definable, the four values are fixed.
_Avoid_: Type, bucket

**mytime Focus category**:
The `Focus` category specifically: hand-tagged as `Time.Focus.Deep` (deep work) or `Time.Focus.Collab.*` (collaboration, e.g. `Time.Focus.Collab.Meeting`). User-entered, hierarchical, and distinct from myday's `focus` grouping below despite sharing label names.
_Avoid_: Focus (unqualified, when myday's grouping could also be meant)

**Time block** (myday):
A single line in a daily note's `## Time` section of the form `HH:MM - HH:MM Type: #ProjectCode Description`, e.g. `09:00 - 12:00 T: #Project-Work Development work`. Represents a scheduled span of wall-clock time, not just a duration.
_Avoid_: Time entry (reserved for mytime's format), time slot

**Type code** (myday):
The single-letter code in a time block (`T`, `M`, `C`, `A`, `L`, `B`) identifying the activity kind: Task, Meeting, Comms, Admin, Learning, Break. Fixed set, not user-definable.
_Avoid_: Activity type (use Type code for the letter, Type name for its expansion)

**Project code** (myday):
The `#ProjectCode` token in a time block, e.g. `#Project-Work`. Free text chosen by the user, used to group time blocks in summaries.
_Avoid_: Tag, label

**myday focus grouping**:
A derived three-way bucketing of time blocks by Type code — Task/Learning → `Deep`, Meeting → `Meeting`, Comms/Admin → `Shallow` — used only by `myday`'s focus summary. Automatically computed, never hand-entered, and distinct from mytime's Focus category above despite sharing label names.
_Avoid_: Focus (unqualified, when mytime's Focus category could also be meant)

**Gap**:
A time range within the `## Time` section of a daily note that isn't covered by any time block, detected by `myday`'s validation.
_Avoid_: Missing time, hole

**Overlap**:
Two time blocks in the same daily note whose `HH:MM - HH:MM` ranges intersect, flagged as a validation error by `myday`.

**Fix** (myday):
`myday`'s in-place rewrite of a daily note's time blocks to close a detected gap, by extending the preceding block's end time forward. Only closes gaps — never touches overlaps, which must be fixed by hand.
_Avoid_: Auto-correct, repair

**Report**:
The tabular or JSON output either tool produces after aggregating a date range of daily notes. `mytime` reports by Category; `myday` reports by project code, Type, or focus grouping.
