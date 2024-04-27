# mytime

A utility for extracting and summarizing time tracking information from daily
notes.

Time tracking information is organized into a hierarchical format which allows
for the collection of different categories of time information. This is useful
because it allows the collection of time spent on individual projects and also
the collection of time spent collaborating or doing deep work.

Time entries are strings of the format: `Time.Category.Name: hours` where
category is one of the following:

- Proj: Project time.
- Area: A more general category type. Useful for grouping projects into themes.
- Focus: Collaboration or Deep Work time.
- Prof: The [four types of professional time](https://www.sahilbloom.com/newsletter/the-4-types-of-professional-time?ref=mattrutherford.co.uk), Management, Creation, Consumption, Ideation.

The time information is entered in hours with decimal fractions supported, e.g. `10.5`.

The `Name` can be any string. It is sometimes useful to make this an extension
of the hierarchical structure, e.g. "Collab.Meeting". It will be treated as a
single string during processing.

`mytime` uses some conventions for the daily notes files that contain the time
tracking information:

- Markdown file format, extension `.md`
- Filename is the date of the daily note in the format: `YYYY-MM-DD.md`

`mytime` provides several options for specifying a time period. Only the daily
note files that lie within the specified time period will be included in the
analysis. If no time period is specified, today's time tracking info will be
analysed.

## Examples

Time information format within the daily note files:

```
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

Getting the summary of *Focus* time from the example files in the examples directory:
```
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



## Installation

Installation uses setuptools to install the utility from a cloned repo.

```bash
git clone https://github.com/stevedoyle/mytime.git
cd mytime
pip install --editable .
```

## Usage

```
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
  --category [Area|Focus|Proj|Prof|All]
                                  Category of time entries to summarise
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
  --help                          Show this message and exit.
```
