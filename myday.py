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
        if line.strip() == TIME_SECTION_HEADER:
            in_time_section = True
            continue
        if in_time_section:
            if line.strip().startswith("#"):
                break
            # Match time block format: START - END Type: #ProjectCode Description
            if re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\s*[TMCALB]:", line.strip()):
                time_section.append(line.strip())
    return time_section


def extract_time_section_for_validation(filename: str) -> List[str]:
    """Extract ALL lines from the time section for validation (including invalid ones)."""
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    time_section = []
    in_time_section = False
    for line in lines:
        if line.strip() == TIME_SECTION_HEADER:
            in_time_section = True
            continue
        if in_time_section:
            if line.strip().startswith("#"):
                break
            # Include all non-empty lines in time section for validation
            if line.strip():
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


def summarize_by_focus(type_totals: Dict[str, int]) -> Dict[str, int]:
    """Summarize total time by productivity focus."""
    focus_totals = defaultdict(int)

    for type_name, minutes in type_totals.items():
        if type_name in ["Task", "Learning"]:
            focus_totals["Deep"] += minutes
        elif type_name in ["Meeting"]:
            focus_totals["Meeting"] += minutes
        elif type_name in ["Comms", "Admin"]:
            focus_totals["Shallow"] += minutes

    return dict(focus_totals)


def format_minutes_to_hours(minutes: int) -> str:
    """Convert minutes to HH:MM format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"


def format_minutes_to_hours_decimal(minutes: int) -> str:
    """Convert minutes to HH:MM format."""
    hours = float(minutes) / 60
    hours = round(hours, 2)  # Round to 2 decimal places
    return f"{hours:g}"


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


def validate_time_entries(time_lines: List[str]) -> List[str]:
    """Validate time entries and return a list of validation errors."""
    errors = []
    parsed_entries = []

    # First pass: Check format and parse valid entries
    for line_num, line in enumerate(time_lines, 1):
        # Check for empty time block format: HH:MM - HH:MM
        empty_match = re.match(r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})$", line)

        # Check for full format: HH:MM - HH:MM Type: Description
        full_match = re.match(
            r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s*([A-Z]):\s*(.*)$", line
        )

        if empty_match:
            # Handle empty time block format
            start_time_str = empty_match.group(1)
            end_time_str = empty_match.group(2)
            type_code = None
            description = ""
        elif full_match:
            # Handle full format
            start_time_str = full_match.group(1)
            end_time_str = full_match.group(2)
            type_code = full_match.group(3)
            description = full_match.group(4).strip()
        else:
            errors.append(f"Line {line_num}: Invalid format - '{line}'")
            continue

        # Validate time format
        try:
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")
        except ValueError:
            errors.append(
                f"Line {line_num}: Invalid time format - '{start_time_str}' or '{end_time_str}'"
            )
            continue

        # Check type code (only if not empty format)
        if type_code is not None and type_code not in TYPE_CODES:
            errors.append(
                f"Line {line_num}: Invalid type code '{type_code}' - must be one of {list(TYPE_CODES.keys())}"
            )
            continue

        # Check if end time is after start time (allowing for crossing midnight)
        if end_time <= start_time:
            # Check if this could be a midnight crossing
            end_time_next_day = end_time + timedelta(days=1)
            duration = end_time_next_day - start_time
            if duration > timedelta(hours=12):  # Unreasonable for a single activity
                errors.append(
                    f"Line {line_num}: End time '{end_time_str}' should be after start time '{start_time_str}'"
                )
                continue

        parsed_entries.append(
            {
                "line_num": line_num,
                "start_time": start_time,
                "end_time": end_time,
                "start_str": start_time_str,
                "end_str": end_time_str,
                "type_code": type_code,
                "description": description,
                "original_line": line,
            }
        )

    # Second pass: Check for overlaps and gaps
    if len(parsed_entries) > 1:
        # Sort entries by start time, handling midnight crossings
        def sort_key(entry):
            # For entries that cross midnight, we need special handling
            start_time = entry["start_time"]
            end_time = entry["end_time"]

            # If end time is before start time, it crosses midnight
            if end_time <= start_time:
                # For sorting purposes, treat early morning times as next day
                if start_time.hour >= 12:  # PM times stay as-is
                    return start_time
                else:  # AM times are treated as next day
                    return start_time + timedelta(days=1)
            else:
                return start_time

        sorted_entries = sorted(parsed_entries, key=sort_key)

        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_entry = sorted_entries[i + 1]

            current_end = current["end_time"]
            next_start = next_entry["start_time"]

            # Handle midnight crossing for current entry
            if current_end <= current["start_time"]:
                current_end = current_end + timedelta(days=1)

            # Handle midnight crossing for next entry
            if next_start < current["start_time"] and current["start_time"].hour >= 12:
                next_start = next_start + timedelta(days=1)

            # Check for overlaps
            if current_end > next_start:
                errors.append(
                    f"Lines {current['line_num']}-{next_entry['line_num']}: "
                    f"Overlapping time blocks - '{current['start_str']}-{current['end_str']}' "
                    f"overlaps with '{next_entry['start_str']}-{next_entry['end_str']}'"
                )

            # Check for gaps (only if no overlap)
            elif current_end < next_start:
                gap_duration = next_start - current_end
                if gap_duration > timedelta(minutes=0):
                    gap_minutes = int(gap_duration.total_seconds() / 60)
                    # Only report gaps if they are reasonable (not due to day boundary issues)
                    if gap_minutes < 12 * 60:  # Less than 12 hours
                        errors.append(
                            f"Lines {current['line_num']}-{next_entry['line_num']}: "
                            f"Gap of {gap_minutes} minutes between '{current['start_str']}-{current['end_str']}' "
                            f"and '{next_entry['start_str']}-{next_entry['end_str']}'"
                        )

    return errors


def fix_time_gaps(filename: str, validation_time_lines: List[str]) -> bool:
    """Fix time gaps in the file by updating end times. Returns True if fixes were made."""
    validation_errors = validate_time_entries(validation_time_lines)
    gap_errors = [error for error in validation_errors if "Gap of" in error]

    if not gap_errors:
        return False

    print(f"Found {len(gap_errors)} time gap(s) to fix:")
    for error in gap_errors:
        print(f"  🔧 {error}")

    # Read the entire file
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the time section and identify lines to fix
    in_time_section = False
    time_line_indices = []  # Store (line_index, time_line_content)

    for i, line in enumerate(lines):
        if line.strip() == TIME_SECTION_HEADER:
            in_time_section = True
            continue
        if in_time_section:
            if line.strip().startswith("#"):
                break
            if line.strip():
                time_line_indices.append((i, line.strip()))

    # Parse entries and identify gaps
    parsed_entries = []
    for line_num, line in enumerate(validation_time_lines, 1):
        # Check for empty time block format: HH:MM - HH:MM
        empty_match = re.match(r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})$", line)

        # Check for full format: HH:MM - HH:MM Type: Description
        full_match = re.match(
            r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s*([A-Z]):\s*(.*)$", line
        )

        if empty_match:
            start_time_str = empty_match.group(1)
            end_time_str = empty_match.group(2)
            type_and_desc = ""
        elif full_match:
            start_time_str = full_match.group(1)
            end_time_str = full_match.group(2)
            type_and_desc = f" {full_match.group(3)}: {full_match.group(4)}"
        else:
            continue

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")

            parsed_entries.append(
                {
                    "line_num": line_num,
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_str": start_time_str,
                    "end_str": end_time_str,
                    "type_and_desc": type_and_desc,
                    "original_line": line,
                }
            )
        except ValueError:
            continue

    # Sort entries and identify gaps to fix
    sorted_entries = sorted(parsed_entries, key=lambda x: x["start_time"])
    fixes_made = 0

    for i in range(len(sorted_entries) - 1):
        current = sorted_entries[i]
        next_entry = sorted_entries[i + 1]

        current_end = current["end_time"]
        next_start = next_entry["start_time"]

        # Handle midnight crossing for current entry
        if current_end <= current["start_time"]:
            current_end = current_end + timedelta(days=1)

        # Handle midnight crossing for next entry
        if next_start < current["start_time"] and current["start_time"].hour >= 12:
            next_start = next_start + timedelta(days=1)

        # Check for gap
        if current_end < next_start:
            gap_duration = next_start - current_end
            if gap_duration > timedelta(minutes=0) and gap_duration < timedelta(
                hours=12
            ):
                # Fix the gap by updating the end time of the current entry
                new_end_time = next_entry["start_str"]

                # Find the line in the original file and update it
                line_index = time_line_indices[current["line_num"] - 1][0]

                # Replace the end time in the line
                if current["type_and_desc"]:
                    new_line = f"{current['start_str']} - {new_end_time}{current['type_and_desc']}\n"
                else:
                    new_line = f"{current['start_str']} - {new_end_time}\n"

                lines[line_index] = new_line
                fixes_made += 1

                print(
                    f"  ✅ Fixed gap: Updated '{current['start_str']}-{current['end_str']}' to '{current['start_str']}-{new_end_time}'"
                )

    if fixes_made > 0:
        # Write the fixed content back to the file
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"\n🎉 Applied {fixes_made} fix(es) to {filename}")
        return True
    else:
        print("\n⚠️  No gaps could be fixed automatically")
        return False


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
@click.option(
    "--validate",
    is_flag=True,
    default=False,
    help="Validate time entries for gaps, overlaps, and formatting errors",
)
@click.option(
    "--fix",
    is_flag=True,
    default=False,
    help="Fix time gaps by updating end times (requires --validate)",
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
    validate,
    fix,
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

    # Validate time entries if requested
    if validate or fix:
        if fix and not validate:
            # --fix requires --validate
            click.echo(
                "Error: --fix option requires --validate option to be specified",
                err=True,
            )
            sys.exit(1)

        validation_time_lines = extract_time_section_for_validation(filename_to_use)
        validation_errors = validate_time_entries(validation_time_lines)

        if fix and validation_errors:
            # Try to fix gaps first
            fixes_made = fix_time_gaps(filename_to_use, validation_time_lines)
            if fixes_made:
                # Re-validate after fixes
                validation_time_lines = extract_time_section_for_validation(
                    filename_to_use
                )
                validation_errors = validate_time_entries(validation_time_lines)
                # Re-extract time lines after fixes
                time_lines = extract_time_section(filename_to_use)

        if validation_errors:
            print(f"Validation errors found in {filename_to_use}:")
            for error in validation_errors:
                print(f"  ❌ {error}")
            print(f"\nTotal errors: {len(validation_errors)}")
            if fix:
                print("⚠️  Some errors could not be fixed automatically")
            sys.exit(1)
        else:
            print(f"✅ No validation errors found in {filename_to_use}")
            if not validation_time_lines:
                print("📝 No time entries found in the file.")
                return

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
            for project, minutes in sorted(
                project_totals.items(), key=lambda x: x[1], reverse=True
            )
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
            for type_name, minutes in sorted(
                type_totals.items(), key=lambda x: x[1], reverse=True
            )
        ]
        print(tabulate(type_table, headers=["Type", "Total Time"], tablefmt="github"))

        print("\n## Summary by Productivity Focus")
        focus_totals = summarize_by_focus(type_totals)
        focus_table = [
            [focus, format_minutes_to_hours(minutes)]
            for focus, minutes in sorted(
                focus_totals.items(), key=lambda x: x[1], reverse=True
            )
        ]
        print(
            tabulate(
                focus_table,
                headers=["Productivity", "Total Time"],
                tablefmt="github",
            )
        )

        # Print summaries with formatting
        print("\nProjects:")
        for project, minutes in sorted(
            project_totals.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"- Time.Proj.{project}: {format_minutes_to_hours_decimal(minutes)}")

        print("\nTypes:")
        for type_name, minutes in sorted(
            type_totals.items(), key=lambda x: x[1], reverse=True
        ):
            print(
                f"- Time.Type.{type_name}: {format_minutes_to_hours_decimal(minutes)}"
            )

        print("\nProductivity:")
        for focus, minutes in sorted(
            focus_totals.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"- Time.Focus.{focus}: {format_minutes_to_hours_decimal(minutes)}")

        # Print overall total
        total_hours, total_rem_minutes = calculate_total_time(entries, include_breaks)
        print(f"\nTotal time: {total_hours}:{total_rem_minutes:02d}")
    else:
        print("No activities match the filter.")


if __name__ == "__main__":
    main()
