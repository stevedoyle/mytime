import os
import re
import sys
from datetime import date, datetime, timedelta
from typing import List, Dict
from collections import defaultdict

import click
from tabulate import tabulate

TIME_SECTION_HEADER = "## Time"
BREAK_ACTIVITY_ID = "Break"

# Type codes mapping
TYPE_CODES = {
    "T": "Task",
    "M": "Meeting",
    "C": "Comms",
    "A": "Admin",
    "L": "Learning",
    "B": "Break",
}


def extract_time_section(filename: str) -> List[str]:
    """Extract the time section from the given markdown file."""
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    time_section = []
    in_time_section = False
    for line in lines:
        if line.strip().startswith(TIME_SECTION_HEADER):
            in_time_section = True
            continue
        if in_time_section:
            if line.strip().startswith("#"):
                break
            # Match time block format: START - END Type: #ProjectCode Description
            if re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\s*[TMCALB]:", line.strip()):
                time_section.append(line.strip())
    return time_section


def parse_time_entries(time_lines: List[str]) -> List[List[str]]:
    """Parse time entries from the time section of the file."""
    entries = []

    for line in time_lines:
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
            project_match = re.search(r"#(\w+(?:-\w+)*)", description)

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
            clean_description = re.sub(r"#\w+(?:-\w+)*", "", description).strip()

            entries.append(
                [
                    start_time,
                    duration_str,
                    TYPE_CODES.get(type_code, type_code),
                    project,
                    clean_description,
                ]
            )

    return entries


def summarize_by_project(entries: List[List[str]]) -> Dict[str, int]:
    """Summarize total time by project."""
    project_totals = defaultdict(int)

    for entry in entries:
        duration_str = entry[1]
        project = entry[3]

        if duration_str != "-":
            h, m = map(int, duration_str.split(":"))
            total_minutes = h * 60 + m
            project_totals[project] += total_minutes

    return dict(project_totals)


def summarize_by_type(entries: List[List[str]]) -> Dict[str, int]:
    """Summarize total time by type."""
    type_totals = defaultdict(int)

    for entry in entries:
        duration_str = entry[1]
        type_name = entry[2]

        if duration_str != "-":
            h, m = map(int, duration_str.split(":"))
            total_minutes = h * 60 + m
            type_totals[type_name] += total_minutes

    return dict(type_totals)


def format_minutes_to_hours(minutes: int) -> str:
    """Convert minutes to HH:MM format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"


def filter_entries(
    entries: List[List[str]], filter_text: str, ignore_case: bool = False
) -> List[List[str]]:
    """Filter entries based on a regular expression."""
    if filter_text:
        try:
            flags = re.IGNORECASE if ignore_case else 0
            filter_re = re.compile(filter_text, flags)
        except re.error as e:
            click.echo(f"Error: Invalid regular expression for --filter: {e}", err=True)
            sys.exit(1)
        return [
            row for row in entries if filter_re.search(row[4])
        ]  # Search in description
    return entries


def ignore_entries(
    entries: List[List[str]], ignore_text: str, ignore_case: bool = False
) -> List[List[str]]:
    """Exclude entries based on a regular expression."""
    if ignore_text:
        try:
            flags = re.IGNORECASE if ignore_case else 0
            ignore_re = re.compile(ignore_text, flags)
        except re.error as e:
            click.echo(f"Error: Invalid regular expression for --ignore: {e}", err=True)
            sys.exit(1)
        return [
            row for row in entries if not ignore_re.search(row[4])
        ]  # Search in description
    return entries


def calculate_total_time(
    entries: List[List[str]], include_breaks: bool = False
) -> tuple[int, int]:
    """Calculate total time spent on activities, optionally including breaks."""
    total_minutes = 0
    for entry in entries:
        duration_str = entry[1]
        type_name = entry[2]

        if duration_str != "-" and (include_breaks or type_name != "Break"):
            h, m = map(int, duration_str.split(":"))
            total_minutes += h * 60 + m

    total_hours = total_minutes // 60
    total_rem_minutes = total_minutes % 60
    return total_hours, total_rem_minutes


@click.command()
@click.argument("filename", required=False)
@click.option("--today", is_flag=True, help="Summarize today's file")
@click.option("--yesterday", is_flag=True, help="Summarize yesterday's file")
@click.option(
    "--filter",
    "filter_text",
    default=None,
    help="Only output activities matching this regular expression",
)
@click.option(
    "--ignore-case",
    is_flag=True,
    default=False,
    help="Make the filter regular expression case-insensitive",
)
@click.option(
    "--ignore",
    "ignore_text",
    default=None,
    help="Exclude activities matching this regular expression",
)
@click.option(
    "--ignore-empty",
    is_flag=True,
    default=False,
    help="Ignore activities with an empty name",
)
@click.option(
    "--path",
    "base_path",
    default=".",
    show_default=True,
    help="Base directory to search for files",
)
@click.option(
    "--include-breaks",
    is_flag=True,
    default=False,
    help='Include activities containing "Break" in total time calculation',
)
def main(
    filename,
    today,
    yesterday,
    filter_text,
    ignore_case,
    ignore_text,
    ignore_empty,
    base_path,
    include_breaks,
):
    """Summarize time entries from a markdown file.
    If no filename is provided, defaults to today's file.
    If --today or --yesterday is specified, uses the respective file.
    """
    today_str = date.today().strftime("%Y-%m-%d.md")
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d.md")

    if today:
        filename_to_use = today_str
    elif yesterday:
        filename_to_use = yesterday_str
    elif filename:
        base_filename = os.path.basename(filename)
        if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", base_filename):
            filename_to_use = filename
        else:
            click.echo(
                "Error: Filename must be in the format YYYY-MM-DD.md (optionally with a directory path)",
                err=True,
            )
            sys.exit(1)
    else:
        filename_to_use = today_str

    # Use base_path for file lookup
    if not os.path.isabs(filename_to_use):
        filename_to_use = os.path.join(base_path, filename_to_use)

    if not os.path.exists(filename_to_use):
        click.echo(f"Error: File '{filename_to_use}' does not exist.", err=True)
        sys.exit(1)

    time_lines = extract_time_section(filename_to_use)
    entries = parse_time_entries(time_lines)
    entries = filter_entries(entries, filter_text, ignore_case)
    entries = ignore_entries(entries, ignore_text, ignore_case)
    if ignore_empty:
        entries = [row for row in entries if row[4].strip() != ""]

    if entries:
        # Print detailed entries
        print(
            tabulate(
                entries,
                headers=[
                    "Time",
                    "Duration",
                    "Type",
                    "Project",
                    "Description",
                ],
                tablefmt="github",
            )
        )

        # Print summaries
        print("\n## Summary by Project")
        project_totals = summarize_by_project(entries)
        project_table = [
            [project, format_minutes_to_hours(minutes)]
            for project, minutes in sorted(project_totals.items())
        ]
        print(
            tabulate(
                project_table, headers=["Project", "Total Time"], tablefmt="github"
            )
        )

        print("\n## Summary by Type")
        type_totals = summarize_by_type(entries)
        type_table = [
            [type_name, format_minutes_to_hours(minutes)]
            for type_name, minutes in sorted(type_totals.items())
        ]
        print(tabulate(type_table, headers=["Type", "Total Time"], tablefmt="github"))

        # Print overall total
        total_hours, total_rem_minutes = calculate_total_time(entries, include_breaks)
        print(f"\nTotal time: {total_hours}:{total_rem_minutes:02d}")
    else:
        print("No activities match the filter.")


if __name__ == "__main__":
    main()
