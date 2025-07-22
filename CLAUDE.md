# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based time tracking utility that provides two complementary CLI tools:
- **`mytime`**: Analyzes hierarchical time tracking data in the format `Time.Category.Name: hours`
- **`myday`**: Analyzes structured time blocks with validation and automatic gap fixing

The project uses modern Python packaging with `pyproject.toml`, includes comprehensive test coverage, and follows consistent code formatting standards.

## Development Commands

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_mytime.py
pytest tests/test_myday.py

# Run tests with verbose output
pytest tests/ -v

# Run tests matching a pattern
pytest tests/ -k "fix_time_gaps"
```

### Code Quality
```bash
# Format code with ruff
ruff format .

# Lint and auto-fix with ruff
ruff check --fix .

# Run pre-commit hooks
pre-commit run --all-files
```

### Installation and Building
```bash
# Install in development mode
pip install --editable .

# Build package
python -m build
```

## Architecture

### Core Modules

**mytime.py** - Main module for hierarchical time tracking analysis:
- `extractTimeData()`: Parses time entries from markdown files using regex pattern `Time\.(\w+)\.(.+):\s*(\d+\.?\d?)`
- `getSummary()`: Aggregates and calculates percentages by category
- `getFilesInRange()`: Finds markdown files within date ranges
- `reportTimeSpent()`: Generates tabular summaries
- Date utility functions for various time periods (today, thisweek, lastmonth, etc.)

**myday.py** - Module for structured time block analysis:
- `extract_time_section()`: Parses time blocks from "## Time" sections
- `parse_time_entries()`: Handles time block format `HH:MM - HH:MM Type: #ProjectCode Description`
- `validate_time_entries()`: Detects gaps, overlaps, and formatting errors
- `fix_time_gaps()`: Automatically extends end times to close gaps
- `summarize_by_focus()`: Groups activities by project codes

### Data Flow

1. **File Discovery**: Both tools scan for markdown files with pattern `YYYY-MM-DD.md`
2. **Content Extraction**: Parse time entries using tool-specific patterns
3. **Data Processing**: Aggregate, validate, and transform time data
4. **Output Generation**: Format results as tables (tabulate library) or CSV/TSV

### Time Entry Formats

**mytime format**: `Time.Category.Name: hours`
- Categories: Proj, Area, Focus, Prof
- Example: `Time.Proj.Example1: 3.5`

**myday format**: `HH:MM - HH:MM Type: #ProjectCode Description`
- Type codes: T (Task), M (Meeting), C (Comms), A (Admin), L (Learning), B (Break)
- Example: `09:00 - 12:00 T: #Project-Work Development work`

## Configuration Files

- **pyproject.toml**: Main project configuration with hatchling build backend, ruff formatting rules (88 char line length, double quotes), and project metadata
- **.pre-commit-config.yaml**: Pre-commit hooks including ruff linter/formatter and black
- **requirements.txt**: Pinned production dependencies

## Dependencies

Core runtime dependencies: Click, python-dateutil, tabulate, pandas, pendulum, numpy
Development dependencies: pytest
Code quality: ruff (linting/formatting), black (formatting), pre-commit hooks

## Testing Strategy

- Unit tests for both main modules using pytest
- Mock file operations for isolated testing
- Time manipulation testing with pendulum library
- Validation logic testing for gap detection and fixing

## Development Workflow

1. Before making any changes, create and checkout a feature branch named `feature-[brief-description]`
2. Write comprehensive tests for all new functionality
3. Run all tests before committing
4. Write detailed commit messages explaining the changes and rationale
5. Run `ruff format .` and `ruff check --fix .` before committing
6. Ensure pre-commit hooks pass (automatically runs ruff, black, and other checks)
7. Commit all changes to the feature branch

## Release Workflow

### Overview
Use temporary `release/vX.Y.Z` branches to prepare, validate, and finalize releases before merging to main.

### Release Process

Follow this 6-step process for consistent, validated releases:

#### 1. Create Release Branch
```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create release branch
git checkout -b release/v0.8.2
```

#### 2. Prepare Release
```bash
# Bump package version with Hatch
hatch version patch  # or minor/major

# Update tool versions manually if needed
# Edit version.py: MYTIME_VERSION, MYDAY_VERSION

# Commit release preparations
git add .
git commit -m "chore(release): Prepare for release v0.8.2"
```

#### 3. Validate Release
```bash
# Run comprehensive tests
pytest tests/ -v

# Validate code quality
ruff check --fix .
ruff format .

# Test package installation
pip install --editable .
mytime --version
myday --version

# Build and test distribution
python -m build
```

#### 4. Create Release PR
```bash
# Tag the release
git tag v0.8.2

# Push branch and tag
git push -u origin release/v0.8.2
git push origin v0.8.2

# Create release PR
gh pr create --title "Release v0.8.2" --body "Release notes..."
```

#### 5. Merge and Cleanup
```bash
# After PR approval, merge to main
gh pr merge --merge

# Clean up
git checkout main
git pull origin main
git branch -D release/v0.8.2
```

#### 6. Create GitHub Release
```bash
# Create GitHub release with detailed notes
gh release create v0.8.2 \
  --title "Release v0.8.2" \
  --notes "$(cat <<'EOF'
## Package Changes
- Package version: 0.8.1 → 0.8.2
- Tool versions unchanged: mytime 0.8.0, myday 0.2.0

## Features & Improvements
- [List new features and improvements]
- [Document bug fixes]
- [Highlight breaking changes if any]

## Installation
```bash
pip install mytime==0.8.2
```

## Validation
- ✅ All tests pass (54/54)
- ✅ Code quality checks pass
- ✅ Package builds successfully
- ✅ Tool versions verified
EOF
)" \
  --verify-tag
```

**Alternative: Release with auto-generated notes**
```bash
# For quick releases with automatic changelog
gh release create v0.8.2 --generate-notes --title "Release v0.8.2"
```

### Version Management
- **Package version**: Managed by Hatch (`hatch version patch/minor/major`)
- **Tool versions**: Manual updates in `version.py` (`MYTIME_VERSION`, `MYDAY_VERSION`)
- **Release tags**: Format `vX.Y.Z` (e.g., `v0.8.2`)
