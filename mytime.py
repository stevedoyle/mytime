# Script for summarizing time tracking information from daily notes.

from version import MYTIME_VERSION
import os
import click
import dateutil
import logging
import pandas as pd
import pendulum
import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from tabulate import tabulate


def extractTimeData(contents, prefix=""):
    td = []

    onsite = False
    onsite_pattern = r"onsite:\s*true"
    if re.search(onsite_pattern, contents):
        onsite = True

    pattern = r"Time\.(\w+)\.(.+):\s*(\d+\.?\d?)"
    mobj = re.findall(pattern, contents)
    for category, name, hours in mobj:
        if prefix:
            td.append([prefix, category, name, float(hours), onsite])
        else:
            td.append([category, name, float(hours), onsite])
    return td


def getSummary(df, category):
    areadf = df.loc[df["Category"] == category].drop(columns=["Category"])
    areadf = areadf.groupby("Name")["Hours"].sum().reset_index()
    areadf = areadf.sort_values(by=["Hours"], ascending=False)
    total = areadf["Hours"].sum()
    areadf["%"] = areadf["Hours"] / total * 100
    return areadf, total


def getFilesInRange(fpath, begin, end):
    begindate = dateutil.parser.parse(begin).date()
    enddate = dateutil.parser.parse(end).date()

    files = []
    with os.scandir(fpath) as it:
        for entry in it:
            if entry.name.endswith(".md") and entry.is_file():
                try:
                    filedate = dateutil.parser.parse(
                        os.path.basename(entry).split(".")[0]
                    ).date()
                    if (begindate <= filedate) and (filedate <= enddate):
                        files.append(entry.path)
                except dateutil.parser.ParserError:
                    continue
    return files


def gettimedata(files):
    timedata = []
    for entry in files:
        with open(entry, encoding="UTF-8") as f:
            name = os.path.splitext(os.path.basename(entry))[0]
            td = extractTimeData(f.read(), prefix=name)
            if len(td) > 0:
                timedata.extend(td)
    df = pd.DataFrame(
        timedata, columns=["Date", "Category", "Name", "Hours", "Onsite"]
    ).astype({"Hours": "float"})
    return df


def getNumDays(df):
    return df["Date"].nunique()


def printTable(table, tsv):
    tblFmt = "github"
    if tsv:
        tblFmt = "tsv"

    print(
        tabulate(
            table,
            headers="keys",
            showindex=False,
            floatfmt=("", ".1f", ".2f"),
            tablefmt=tblFmt,
        )
    )


def reportTimeSpent(path, categories, begin, end, tsv=False, onsite=False, brief=False):
    files = []

    if brief:
        categories = ["Focus"]
    else:
        categories = normalizeCategories(categories)

    try:
        files = getFilesInRange(path, begin, end)
        td = gettimedata(files)
        for category in categories:
            areas, total_hours = getSummary(td, category)
            days = getNumDays(td)
            if total_hours:
                if not brief:
                    printTable(areas, tsv)
                print()
                print(f"Total hours:       {total_hours: >6}")
                print(f"Total days:        {days: >6}")
                print(f"Average hours/day: {total_hours / days: >6.1f}")
                print()

        if days > 0 and onsite:
            onsite_days = getOnsiteDays(td)
            print(
                f"Total onsite days: {onsite_days: >6} ({(onsite_days / days * 100):.0f}%)"
            )
    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


def getOnsiteDays(df):
    onsite = df.loc[df["Onsite"]]
    return onsite["Date"].nunique()


def dumpTimeEntries(path, categories, begin, end):
    categories = normalizeCategories(categories)

    try:
        files = getFilesInRange(path, begin, end)
        td = gettimedata(files)
        td = filterTimeData(td, categories)
        td.to_csv(sys.stdout, index=False)
    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


def filterTimeData(df, categories):
    return df[df["Category"].isin(categories)]


def normalizeCategories(categories):
    # Normalize category strings
    categories = [cat.title() for cat in categories]
    if "All" in categories:
        categories = ["Proj", "Type", "Area", "Focus", "Prof"]
    return categories


def extractTimeBlocks(contents):
    """Extract time block entries from markdown content."""
    time_blocks = []
    lines = contents.split("\n")
    in_time_section = False

    for line in lines:
        line = line.strip()
        if line == "## Time":
            in_time_section = True
            continue
        if in_time_section:
            if line.startswith("#"):
                break
            # Match time block format: START - END Type: #ProjectCode Description
            if re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\s*[TMCALB]:", line):
                time_blocks.append(line)
    return time_blocks


def parseTimeBlocks(time_blocks):
    """Parse time blocks and extract task information grouped by project."""
    tasks_by_project = defaultdict(list)

    for line in time_blocks:
        # Parse format: START - END Type: #ProjectCode Description
        match = re.match(
            r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s*([TMCALB]):\s*(.*)$", line
        )
        if match:
            start_time = match.group(1)
            end_time = match.group(2)
            type_code = match.group(3)
            description = match.group(4).strip()

            # Calculate duration
            t1 = datetime.strptime(start_time, "%H:%M")
            t2 = datetime.strptime(end_time, "%H:%M")
            duration = t2 - t1

            # Handle negative durations (crossing midnight)
            if duration < timedelta(0):
                duration += timedelta(days=1)

            duration_str = str(duration)[:-3]  # Remove seconds

            # Parse project code from description
            # Project tags begin with # and continue until the next whitespace character
            project_match = re.search(r"#(\S+)", description)

            if project_match:
                project_code = project_match.group(1)
                # Handle Project-NAME format
                if project_code.startswith("Project-"):
                    project = project_code[8:]  # Remove "Project-" prefix
                else:
                    # Handle other project codes like General, Managing, Team
                    project = project_code
            else:
                # Default to General if no project code provided
                project = "General"

            # Remove hashtags from description for display
            clean_description = re.sub(r"#\S+", "", description).strip()

            # Map type codes to names
            type_names = {
                "T": "Task",
                "M": "Meeting",
                "C": "Comms",
                "A": "Admin",
                "L": "Learning",
                "B": "Break",
            }
            type_name = type_names.get(type_code, type_code)

            # Skip breaks when grouping tasks
            if type_name != "Break":
                tasks_by_project[project].append(
                    {
                        "time": start_time,
                        "duration": duration_str,
                        "type": type_name,
                        "description": clean_description,
                    }
                )

    return dict(tasks_by_project)


def getTimeBlockData(files):
    """Extract time block data from multiple files."""
    all_tasks = defaultdict(list)

    for filepath in files:
        with open(filepath, encoding="UTF-8") as f:
            filename = os.path.splitext(os.path.basename(filepath))[0]
            content = f.read()
            time_blocks = extractTimeBlocks(content)
            if time_blocks:
                tasks_by_project = parseTimeBlocks(time_blocks)
                for project, tasks in tasks_by_project.items():
                    for task in tasks:
                        task["date"] = filename
                        all_tasks[project].append(task)

    return dict(all_tasks)


def reportTasks(path, begin, end, tsv=False):
    """Report tasks grouped by project from time block entries."""
    try:
        files = getFilesInRange(path, begin, end)
        tasks_by_project = getTimeBlockData(files)

        if not tasks_by_project:
            print("No time block entries found in the specified date range.")
            return

        tblFmt = "tsv" if tsv else "github"

        for project in sorted(tasks_by_project.keys()):
            tasks = tasks_by_project[project]
            print(f"\n## Project: {project}")

            # Prepare table data
            table_data = []
            for task in tasks:
                table_data.append(
                    [
                        task["date"],
                        task["time"],
                        task["duration"],
                        task["type"],
                        task["description"],
                    ]
                )

            print(
                tabulate(
                    table_data,
                    headers=["Date", "Time", "Duration", "Type", "Description"],
                    tablefmt=tblFmt,
                )
            )

            print(f"Total tasks: {len(tasks)}")

    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


def extractNotes(contents):
    """Extract notes from the Notes section of markdown content."""
    notes = []
    lines = contents.split("\n")
    in_notes_section = False

    for line in lines:
        line_stripped = line.strip()
        if line_stripped == "## Notes":
            in_notes_section = True
            continue
        if in_notes_section:
            if line_stripped.startswith("##"):
                break
            # Skip empty lines at the start of notes section
            if not notes and not line_stripped:
                continue
            notes.append(
                line.rstrip()
            )  # Keep original indentation but remove trailing whitespace

    # Remove trailing empty lines
    while notes and not notes[-1].strip():
        notes.pop()

    return notes


def getNotesData(files):
    """Extract notes data from multiple files."""
    notes_by_date = {}

    for filepath in files:
        with open(filepath, encoding="UTF-8") as f:
            filename = os.path.splitext(os.path.basename(filepath))[0]
            content = f.read()
            notes = extractNotes(content)
            if notes:
                notes_by_date[filename] = notes

    return notes_by_date


def reportNotes(path, begin, end):
    """Report notes aggregated by date in reverse chronological order."""
    try:
        files = getFilesInRange(path, begin, end)
        notes_by_date = getNotesData(files)

        if not notes_by_date:
            print("No notes found in the specified date range.")
            return

        print("## Notes Summary")
        print()

        # Sort dates in reverse chronological order (newest first)
        for date in sorted(notes_by_date.keys(), reverse=True):
            notes = notes_by_date[date]
            print(f"### {date}")
            for note_line in notes:
                if note_line.strip():  # Only print non-empty lines
                    print(note_line)
                else:
                    print()  # Preserve empty lines within notes
            print()  # Add spacing between dates

    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


##########################################################################


def get_dates_today():
    today = pendulum.today().to_date_string()
    return today, today


def get_dates_yesterday():
    yesterday = pendulum.yesterday().to_date_string()
    return yesterday, yesterday


def get_dates_thisweek():
    today = pendulum.today()
    start = today.start_of("week").to_date_string()
    end = today.end_of("week").to_date_string()
    return start, end


def get_dates_lastweek():
    lastweek = pendulum.today().subtract(weeks=1)
    start = lastweek.start_of("week").to_date_string()
    end = lastweek.end_of("week").to_date_string()
    return start, end


def get_dates_thismonth():
    today = pendulum.today()
    start = today.start_of("month").to_date_string()
    end = today.end_of("month").to_date_string()
    return start, end


def get_dates_lastmonth():
    lastmonth = pendulum.today().subtract(months=1)
    start = lastmonth.start_of("month").to_date_string()
    end = lastmonth.end_of("month").to_date_string()
    return start, end


def get_dates_thisquarter():
    today = pendulum.today()
    start = today.first_of("quarter").to_date_string()
    end = today.last_of("quarter").to_date_string()
    return start, end


def get_dates_lastquarter():
    lastmonth = pendulum.today().subtract(months=3)
    start = lastmonth.first_of("quarter").to_date_string()
    end = lastmonth.last_of("quarter").to_date_string()
    return start, end


def get_dates_thisyear():
    today = pendulum.today()
    start = today.start_of("year").to_date_string()
    end = today.end_of("year").to_date_string()
    return start, end


def get_dates_lastyear():
    lastyear = pendulum.today().subtract(years=1)
    start = lastyear.start_of("year").to_date_string()
    end = lastyear.end_of("year").to_date_string()
    return start, end


def get_dates(
    start,
    end,
    today,
    yesterday,
    thisweek,
    thismonth,
    thisquarter,
    thisyear,
    lastweek,
    lastmonth,
    lastquarter,
    lastyear,
):
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    if today:
        start, end = get_dates_today()
    elif yesterday:
        start, end = get_dates_yesterday()
    elif thisweek:
        start, end = get_dates_thisweek()
    elif thismonth:
        start, end = get_dates_thismonth()
    elif thisquarter:
        start, end = get_dates_thisquarter()
    elif thisyear:
        start, end = get_dates_thisyear()
    elif lastweek:
        start, end = get_dates_lastweek()
    elif lastmonth:
        start, end = get_dates_lastmonth()
    elif lastquarter:
        start, end = get_dates_lastquarter()
    elif lastyear:
        start, end = get_dates_lastyear()
    return start, end


##########################################################################


@click.command()
@click.version_option(version=MYTIME_VERSION)
@click.option("--log", default="warning", help="Logging level (info, debug)")
@click.option(
    "--path",
    default=".",
    help="Path where the files containing the time tracking data is stored.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--category",
    default=["All"],
    multiple=True,
    help="Category of time entries to summarise",
    type=click.Choice(
        ["Area", "Focus", "Proj", "Prof", "Type", "All"], case_sensitive=False
    ),
)
@click.option(
    "--csv",
    default=False,
    is_flag=True,
    help="Format the output as comma separated values with one row per time entry",
)
@click.option(
    "--tsv",
    default=False,
    is_flag=True,
    help="Format the output as tab separated values",
)
@click.option(
    "--from",
    "from_",
    default=pendulum.today(),
    help="Start of time tracking period (default is today).",
    type=click.DateTime(),
)
@click.option(
    "--to",
    default=pendulum.today(),
    help="End of time tracking period (default is today).",
    type=click.DateTime(),
)
@click.option(
    "--today",
    default=False,
    is_flag=True,
    help="Today's time summary. Overrides --from and --to values.",
)
@click.option(
    "--yesterday",
    default=False,
    is_flag=True,
    help="Yesterday's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisweek",
    default=False,
    is_flag=True,
    help="This week's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thismonth",
    default=False,
    is_flag=True,
    help="This month's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisquarter",
    default=False,
    is_flag=True,
    help="This quarter's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisyear",
    default=False,
    is_flag=True,
    help="This year's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastweek",
    default=False,
    is_flag=True,
    help="Last week's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastmonth",
    default=False,
    is_flag=True,
    help="Last month's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastquarter",
    default=False,
    is_flag=True,
    help="Last quarter's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastyear",
    default=False,
    is_flag=True,
    help="Last year's time summary. Overrides --from and --to values.",
)
@click.option(
    "--onsite",
    default=False,
    is_flag=True,
    help="Include onsite information in the summary.",
)
@click.option(
    "--brief", default=False, is_flag=True, help="Brief summary of time entries."
)
@click.option(
    "--tasks",
    default=False,
    is_flag=True,
    help="Analyze time block entries and group tasks by project.",
)
@click.option(
    "--notes",
    default=False,
    is_flag=True,
    help="Extract and aggregate notes from daily notes in reverse chronological order.",
)
def mytime(
    log,
    path,
    category,
    csv,
    tsv,
    from_,
    to,
    today,
    yesterday,
    thisweek,
    thismonth,
    thisquarter,
    thisyear,
    lastweek,
    lastmonth,
    lastquarter,
    lastyear,
    onsite,
    brief,
    tasks,
    notes,
):
    """Summarize time tracking data.

    Multiple options are provided for specifying the time period. Only the time
    tracking data within the specified time period will be analysed. If no time
    period is specified, today's time tracking info will be analyzed.

    Time tracking information is extracted from 'Daily Note' files which follow
    the convention that there is a separate file for each day and the file name
    follows the pattern: 'YYYY-MM-DD.md', e.g. 2023-10-31.md.
    """
    # Logging setup
    numeric_level = getattr(logging, log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log}")
    logging.basicConfig(format="%(message)s", level=numeric_level)

    # Tune pandas settings
    pd.set_option("display.precision", 2)

    start, end = get_dates(
        from_,
        to,
        today,
        yesterday,
        thisweek,
        thismonth,
        thisquarter,
        thisyear,
        lastweek,
        lastmonth,
        lastquarter,
        lastyear,
    )
    logging.info(f"{start} -> {end}")

    if notes:
        reportNotes(path, start, end)
    elif tasks:
        reportTasks(path, start, end, tsv)
    elif csv:
        dumpTimeEntries(path, category, start, end)
    else:
        reportTimeSpent(path, category, start, end, tsv, onsite, brief)


##########################################################################

if __name__ == "__main__":
    mytime()
