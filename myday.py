import os
import re
import sys
from datetime import date, datetime, timedelta
from litellm import completion
from typing import List, Dict


import click
from tabulate import tabulate

TIME_SECTION_HEADER = "## Time"
BREAK_ACTIVITY_ID = "Break"


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
            if re.match(r"^\d{2}:\d{2}", line.strip()):
                time_section.append(line.strip())
    return time_section


def parse_time_entries(time_lines: List[str]) -> List[List[str]]:
    """Parse time entries from the time section of the file."""
    entries = []
    times = []
    activities = []
    wikilink_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    for line in time_lines:
        match = re.match(r"^(\d{2}:\d{2})\s?(.*)", line)
        if match:
            times.append(match.group(1))
            # Remove markdown wikilinks from activity text
            activity = match.group(2)
            activity = wikilink_pattern.sub(r"\1", activity)
            activities.append(activity)
    durations = []

    for i, _ in enumerate(times):
        if i < len(times) - 1:
            t1 = datetime.strptime(times[i], "%H:%M")
            t2 = datetime.strptime(times[i + 1], "%H:%M")
            duration = t2 - t1
            # Handle negative durations (e.g., if times cross midnight)
            if duration < timedelta(0):
                duration += timedelta(days=1)
            durations.append(str(duration)[:-3])  # Remove seconds
        else:
            durations.append("-")
    for t, a, d in zip(times, activities, durations):
        entries.append([t, d, a])
    return entries


def filter_entries(
    entries: List[List[str]], filter_text: str, ignore_case: bool = False
) -> List:
    """Filter entries based on a regular expression."""
    if filter_text:
        try:
            flags = re.IGNORECASE if ignore_case else 0
            filter_re = re.compile(filter_text, flags)
        except re.error as e:
            click.echo(f"Error: Invalid regular expression for --filter: {e}", err=True)
            sys.exit(1)
        return [row for row in entries if filter_re.search(row[2])]
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
        return [row for row in entries if not ignore_re.search(row[2])]
    return entries


def calculate_total_time(
    entries: List[List[str]], include_breaks: bool = False
) -> tuple[int, int]:
    """Calculate total time spent on activities, optionally including breaks."""
    total_minutes = 0
    for _, duration, activity in entries:
        if duration != "-" and (
            include_breaks or not activity.strip().startswith(BREAK_ACTIVITY_ID)
        ):
            h, m = map(int, duration.split(":"))
            total_minutes += h * 60 + m
    total_hours = total_minutes // 60
    total_rem_minutes = total_minutes % 60
    return total_hours, total_rem_minutes


def config_api_key():
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key is None:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    os.environ["GOOGLE_API_KEY"] = api_key


def generate_response(messages: List[Dict]) -> str:
    response = completion(
        model="gemini/gemini-1.5-flash",
        messages=messages,
        max_tokens=1024,
        temperature=0.2,
    )
    if not response or not response.choices:  # type: ignore
        raise ValueError("No response received from the model.")

    first_choice = response.choices[0]  # type: ignore
    if not first_choice.message or not first_choice.message.content:  # type: ignore
        raise ValueError("No message in the first choice of the response.")

    return first_choice.message.content.strip()  # type: ignore


def do_ai_analysis(entries: List[List[str]]) -> None:
    """AI analysis of Time Data."""
    # This function sends the time entries to an AI LLM for analysis.

    timedata = "\n".join(f"{row[0]}, {row[1]}, {row[2]}" for row in entries)
    config_api_key()

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that analyzes time blocks for productivity."
            "The format of each time entry is 'Start time, Duration, Description'"
            "You will categorize each time block entry spent into four types: management, creation, consumption, and ideation."
            "You will treat entry descriptions containing the word 'Break.' as a separate category."
            "Ignore any entries with '-' as the duration."
            "Treat entries with empty descriptions as if they were part of the previous entry."
            "You will summarise the results in a table format with the following columns: "
            "Type, Time Spent, and Description."
            "You will also provide a total time spent at the end of the table.",
        },
        {"role": "user", "content": timedata},
    ]

    four_types_response = generate_response(messages)
    print(four_types_response)


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
    "--ai",
    is_flag=True,
    default=False,
    help="Send time information to an AI analysis method",
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
    ai,
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
        entries = [row for row in entries if row[2].strip() != ""]

    if ai:
        do_ai_analysis(entries)
        return

    if entries:
        print(
            tabulate(
                entries, headers=["Time", "Duration", "Activity"], tablefmt="github"
            )
        )
        total_hours, total_rem_minutes = calculate_total_time(entries, include_breaks)
        print(f"\nTotal time: {total_hours}:{total_rem_minutes:02d}")
    else:
        print("No activities match the filter.")


if __name__ == "__main__":
    main()
