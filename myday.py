import re
import sys
import os
import click
from tabulate import tabulate
from datetime import datetime, timedelta, date

def extract_time_section(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    time_section = []
    in_time_section = False
    for line in lines:
        if line.strip().startswith('## Time'):
            in_time_section = True
            continue
        if in_time_section:
            if line.strip().startswith('##') or line.strip().startswith('# '):
                break
            if re.match(r'^\d{2}:\d{2}', line.strip()):
                time_section.append(line.strip())
    return time_section

def parse_time_entries(time_lines):
    entries = []
    times = []
    activities = []
    wikilink_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    for line in time_lines:
        match = re.match(r'^(\d{2}:\d{2})\s+(.*)', line)
        if match:
            times.append(match.group(1))
            # Remove markdown wikilinks from activity text
            activity = match.group(2)
            activity = wikilink_pattern.sub(r'\1', activity)
            activities.append(activity)
    durations = []
    for i in range(len(times)):
        if i < len(times) - 1:
            t1 = datetime.strptime(times[i], '%H:%M')
            t2 = datetime.strptime(times[i+1], '%H:%M')
            duration = t2 - t1
            # Handle negative durations (e.g., if times cross midnight)
            if duration < timedelta(0):
                duration += timedelta(days=1)
            durations.append(str(duration)[:-3])  # Remove seconds
        else:
            durations.append('-')
    for t, a, d in zip(times, activities, durations):
        entries.append([t, d, a])
    return entries

@click.command()
@click.argument('filename', required=False)
@click.option('--today', is_flag=True, help="Summarize today's file")
@click.option('--yesterday', is_flag=True, help="Summarize yesterday's file")
@click.option('--filter', 'filter_text', default=None, help="Only output activities matching this regular expression")
def main(filename, today, yesterday, filter_text):
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
            click.echo("Error: Filename must be in the format YYYY-MM-DD.md (optionally with a directory path)", err=True)
            sys.exit(1)
    else:
        filename_to_use = today_str

    if not os.path.exists(filename_to_use):
        click.echo(f"Error: File '{filename_to_use}' does not exist.", err=True)
        sys.exit(1)

    time_lines = extract_time_section(filename_to_use)
    entries = parse_time_entries(time_lines)

    # Apply filter if specified (now as regex)
    if filter_text:
        try:
            filter_re = re.compile(filter_text)
        except re.error as e:
            click.echo(f"Error: Invalid regular expression for --filter: {e}", err=True)
            sys.exit(1)
        entries = [row for row in entries if filter_re.search(row[2])]

    if entries:
        print(tabulate(entries, headers=["Time", "Duration", "Activity"], tablefmt="github"))
        # Recalculate total time for filtered entries
        total_minutes = 0
        for t, d, a in entries:
            if d != '-' and not a.strip().startswith('Break'):
                h, m = map(int, d.split(':'))
                total_minutes += h * 60 + m
        total_hours = total_minutes // 60
        total_rem_minutes = total_minutes % 60
        print(f"\nTotal time (excluding Breaks): {total_hours}:{total_rem_minutes:02d}")
    else:
        print("No activities match the filter.")

if __name__ == "__main__":
    main()
