---
status: accepted
date: 2026-08-16
---

# Package version and per-tool versions are tracked independently

The distributed package has one version (`__version__` in `version.py`, driven by `hatch version`), but `mytime` and `myday` each carry their own version number (`MYTIME_VERSION`, `MYDAY_VERSION`) reported by `--version` and bumped by hand per release based on which tool actually changed. Three version numbers for one PyPI package is surprising until you know it's deliberate: the package version tracks *releases* (what you `pip install`), while the tool versions track each CLI's own feature/behavior history independently of the other tool's changes — a release that only touches `myday` doesn't inflate `mytime`'s version, and vice versa.

The cost is manual bookkeeping: the release workflow requires deciding, per tool, whether its version needs a bump, rather than a single number auto-tracking everything.
