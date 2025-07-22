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
