# mytime

A comprehensive utility for extracting and summarizing time tracking information from daily notes. This package provides two complementary tools:

- **`mytime`**: Analyzes hierarchical time tracking data in the format `Time.Category.Name: hours`
- **`myday`**: Analyzes structured time blocks with validation and automatic gap fixing

## When to Use Which Tool

- **Use `mytime`** when you want to:
  - Analyze time tracking data across multiple days/weeks/months
  - Categorize time by projects, areas, focus types, or professional activities
  - Get high-level summaries and percentages
  - Export data to CSV for further analysis

- **Use `myday`** when you want to:
  - Analyze detailed time blocks for a single day
  - Validate time entries for gaps, overlaps, or formatting errors
  - Automatically fix time gaps in your daily schedule
  - Work with structured time blocks that include activity types and project codes

## mytime Tool

### Overview

The `mytime` tool extracts and summarizes time tracking information organized in a hierarchical format. This allows for the collection of different categories of time information, useful for tracking time spent on individual projects as well as collaboration or deep work.

Time entries are strings of the format: `Time.Category.Name: hours` where category is one of the following:

- **Proj**: Project time
- **Area**: A more general category type. Useful for grouping projects into themes
- **Focus**: Collaboration or Deep Work time
- **Prof**: The [four types of professional time](https://www.sahilbloom.com/newsletter/the-4-types-of-professional-time?ref=mattrutherford.co.uk) - Management, Creation, Consumption, Ideation

The time information is entered in hours with decimal fractions supported, e.g. `10.5`.

### Time Format Examples

Time information format within the daily note files:

```text
Time.Proj.Example1: 3.5
Time.Proj.Exmaple2: 2

Time.Area.Theme1: 2.5
Time.Area.Managing: 1.5
Time.Area.Overhead: 4

Time.Focus.Collab.Meeting: 3
Time.Focus.Collab.Other: 2
Time.Focus.Deep: 5

Time.Prof.Management: 3
Time.Prof.Creation: 2
Time.Prof.Consumption: 1.5
Time.Prof.Ideation: 0
```

### Usage Example

Getting the summary of *Focus* time from the example files in the examples directory:

```bash
mytime --path=./examples --from 2023-10-16 --to 2023-10-20 --category=Focus
```

Output:

```text
| Name           |   Hours |     % |
|----------------|---------|-------|
| Collab.Meeting |     9.0 | 50.00 |
| Deep           |     6.5 | 36.11 |
| Collab.Other   |     2.5 | 13.89 |
```

## myday Tool

### Time Block Analysis

The `myday` tool analyzes structured time blocks in markdown files. It supports validation and automatic fixing of time gaps, making it ideal for detailed daily time tracking.

### Time Block Format

Time blocks use the format: `HH:MM - HH:MM Type: #ProjectCode Description`

**Type codes:**
- **T**: Task
- **M**: Meeting
- **C**: Communications
- **A**: Administrative
- **L**: Learning
- **B**: Break

**Example time blocks:**

```text
## Time
08:00 - 09:00 T: #General Morning routine
09:00 - 12:00 T: #Project-Work Development work
12:00 - 13:00 B: #General Lunch break
13:00 - 14:00 M: #Team Weekly standup
14:00 - 17:00 T: #Project-Work Continue development
```

### Empty Time Blocks

The tool also supports empty time blocks (just timestamps):

```text
## Time
09:00 - 10:00
10:00 - 11:30 T: #Project-Work Development work
11:30 - 12:00
```

### Validation and Fixing

The `myday` tool includes powerful validation features:

- **Gap detection**: Identifies time gaps between consecutive entries
- **Overlap detection**: Finds overlapping time blocks
- **Format validation**: Checks for proper time and format syntax
- **Automatic fixing**: Can automatically extend end times to close gaps

```bash
# Validate time entries
myday --validate 2025-07-18.md

# Validate and automatically fix gaps
myday --validate --fix 2025-07-18.md
```

## File Conventions

Both tools use markdown files with specific conventions:

- **File format**: Markdown (`.md` extension)
- **Filename pattern**: `YYYY-MM-DD.md` (e.g., `2023-10-31.md`)
- **Directory structure**: Files can be organized in any directory structure



## Installation

Installation uses setuptools to install the utility from a cloned repo.

```bash
git clone https://github.com/stevedoyle/mytime.git
cd mytime
pip install --editable .
```

## Usage

### mytime Command

```text
Usage: mytime [OPTIONS]

  Summarize time tracking data.

  Multiple options are provided for specifying the time period. Only the time
  tracking data within the specified time period will be analysed. If no time
  period is specified, today's time tracking info will be analyzed.

  Time tracking information is extracted from 'Daily Note' files which follow
  the convention that there is a separate file for each day and the file name
  follows the pattern: 'YYYY-MM-DD.md', e.g. 2023-10-31.md.

Options:
  --version                       Show the version and exit.
  --log TEXT                      Logging level (info, debug)
  --path DIRECTORY                Path where the files containing the time
                                  tracking data is stored.
  --category [Area|Focus|Proj|Prof|Type|All]
                                  Category of time entries to summarise
  --csv                           Format the output as comma separated values
                                  with one row per time entry
  --tsv                           Format the output as tab separated values
  --from [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Start of time tracking period (default is
                                  today).
  --to [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  End of time tracking period (default is
                                  today).
  --today                         Today's time summary. Overrides --from and
                                  --to values.
  --yesterday                     Yesterday's time summary. Overrides --from
                                  and --to values.
  --thisweek                      This week's time summary. Overrides --from
                                  and --to values.
  --thismonth                     This month's time summary. Overrides --from
                                  and --to values.
  --thisquarter                   This quarter's time summary. Overrides
                                  --from and --to values.
  --thisyear                      This year's time summary. Overrides --from
                                  and --to values.
  --lastweek                      Last week's time summary. Overrides --from
                                  and --to values.
  --lastmonth                     Last month's time summary. Overrides --from
                                  and --to values.
  --lastquarter                   Last quarter's time summary. Overrides
                                  --from and --to values.
  --lastyear                      Last year's time summary. Overrides --from
                                  and --to values.
  --onsite                        Include onsite information in the summary.
  --brief                         Brief summary of time entries.
  --help                          Show this message and exit.
```

### myday Command

```text
Usage: myday.py [OPTIONS] [FILENAME]

  Summarize time entries from a markdown file. If no filename is provided,
  defaults to today's file. If --today or --yesterday is specified, uses the
  respective file.

Options:
  --today           Summarize today's file
  --yesterday       Summarize yesterday's file
  --filter TEXT     Only output activities matching this regular expression
  --ignore-case     Make the filter regular expression case-insensitive
  --ignore TEXT     Exclude activities matching this regular expression
  --ignore-empty    Ignore activities with an empty name
  --path TEXT       Base directory to search for files  [default: .]
  --include-breaks  Include activities containing "Break" in total time
                    calculation
  --validate        Validate time entries for gaps, overlaps, and formatting
                    errors
  --fix             Fix time gaps by updating end times (requires --validate)
  --help            Show this message and exit.
```

### Usage Examples

**mytime examples:**

```bash
# Analyze today's time tracking data
mytime

# Analyze a specific time period
mytime --from 2023-10-16 --to 2023-10-20

# Focus on specific categories
mytime --category Focus --category Proj

# Export to CSV
mytime --csv --from 2023-10-01 --to 2023-10-31
```

**myday examples:**

```bash
# Summarize today's time blocks
myday

# Analyze a specific file
myday 2023-10-16.md

# Validate time entries for errors
myday --validate 2023-10-16.md

# Validate and automatically fix gaps
myday --validate --fix 2023-10-16.md

# Filter activities and ignore breaks
myday --filter "Project-Work" --ignore-empty
```

## Testing

The project includes comprehensive test coverage with pytest:

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_myday.py
pytest tests/test_mytime.py

# Run tests with verbose output
pytest tests/ -v

# Run only fix-related tests
pytest tests/ -k "fix_time_gaps"
```
