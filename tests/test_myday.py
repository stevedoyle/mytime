import tempfile
import os
from myday import (
    extract_time_section,
    parse_time_entries,
    calculate_total_time,
    filter_entries,
    ignore_entries,
)


class TestMyDay:
    def test_extract_time_section_basic(self):
        content = """# My Day

Some intro text.

## Time
08:00 - 09:00 T: #General Breakfast
09:00 - 12:00 T: #Project-Work Work on project
12:00 - 13:00 B: #General Lunch
13:00 - 14:00 M: #Team Meeting
# Notes
Some notes here.
"""

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
            tmp.write(content)
            tmp_filename = tmp.name

        try:
            result = extract_time_section(tmp_filename)
            assert result == [
                "08:00 - 09:00 T: #General Breakfast",
                "09:00 - 12:00 T: #Project-Work Work on project",
                "12:00 - 13:00 B: #General Lunch",
                "13:00 - 14:00 M: #Team Meeting",
            ]
        finally:
            os.remove(tmp_filename)

    def test_extract_time_section_no_time_section(self):
        content = """# My Day

08:00 - 09:00 T: #General Breakfast
09:00 - 12:00 T: #Project-Work Work on project
"""

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
            tmp.write(content)
            tmp_filename = tmp.name

        try:
            result = extract_time_section(tmp_filename)
            assert result == []
        finally:
            os.remove(tmp_filename)

    def test_parse_time_entries_basic(self):
        time_lines = [
            "08:00 - 09:00 T: #General Breakfast",
            "09:00 - 12:00 T: #Project-Work Work on project",
            "12:00 - 13:00 B: #General Lunch",
            "13:00 - 14:00 M: #Team Meeting",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "1:00", "Meeting", "Team", "Meeting"],
        ]

    def test_parse_time_entries_with_no_project(self):
        time_lines = [
            "08:00 - 09:00 T: Breakfast",
            "09:00 - 12:00 T: Work on project",
            "12:00 - 13:00 B: Lunch",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "General", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
        ]

    def test_calculate_total_time(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Email"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]
        # Should sum only durations that are not "-" and not "Break"
        total_hours, total_rem_minutes = calculate_total_time(entries)
        assert total_hours == 4
        assert total_rem_minutes == 0

    def test_calculate_total_time_with_break(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Email"],
            ["09:00", "0:30", "Break", "General", "Coffee break"],
            ["09:30", "2:00", "Task", "Work", "Work on project"],
            ["11:30", "-", "Meeting", "Team", "Meeting"],
        ]
        # Should skip the "Break" entry
        total_hours, total_rem_minutes = calculate_total_time(entries)
        assert total_hours == 3
        assert total_rem_minutes == 0

    def test_filter_entries_case_sensitive(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]
        filtered = filter_entries(entries, "work", ignore_case=False)
        # Should not match "Work on project" because of case
        assert filtered == []

    def test_filter_entries_ignore_case(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]
        filtered = filter_entries(entries, "work", ignore_case=True)
        # Should match "Work on project" because ignore_case=True
        assert filtered == [["09:00", "3:00", "Task", "Work", "Work on project"]]

    def test_ignore_entries(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]
        # Ignore activities containing "Work"
        ignored = ignore_entries(entries, "Work", ignore_case=False)
        assert ignored == [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["12:00", "1:00", "Break", "General", "Lunch"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]

        # Ignore activities containing "lunch" (case-insensitive)
        ignored = ignore_entries(entries, "lunch", ignore_case=True)
        assert ignored == [
            ["08:00", "1:00", "Task", "General", "Breakfast"],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]

    def test_calculate_total_time_include_breaks(self):
        entries = [
            ["08:00", "1:00", "Task", "General", "Email"],
            ["09:00", "0:30", "Break", "General", "Coffee break"],
            ["09:30", "2:00", "Task", "Work", "Work on project"],
            ["11:30", "-", "Meeting", "Team", "Meeting"],
        ]
        # With include_breaks=True, "Break" entry should be included in total
        total_hours, total_rem_minutes = calculate_total_time(
            entries, include_breaks=True
        )
        assert total_hours == 3
        assert total_rem_minutes == 30

    def test_ignore_empty(self):
        entries = [
            ["08:00", "1:00", "Task", "General", ""],
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["12:00", "1:00", "Break", "General", " "],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]
        # Simulate --ignore-empty by filtering out entries with empty or whitespace-only description
        filtered = [row for row in entries if row[4].strip() != ""]
        assert filtered == [
            ["09:00", "3:00", "Task", "Work", "Work on project"],
            ["13:00", "-", "Meeting", "Team", "Meeting"],
        ]

    def test_parse_project_codes(self):
        time_lines = [
            "08:00 - 09:00 T: #General General task",
            "09:00 - 10:00 T: #Managing Management task",
            "10:00 - 11:00 T: #Team Team task",
            "11:00 - 12:00 T: #Project-MyProject Work on my project",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Task", "General", "General task"],
            ["09:00", "1:00", "Task", "Managing", "Management task"],
            ["10:00", "1:00", "Task", "Team", "Team task"],
            ["11:00", "1:00", "Task", "MyProject", "Work on my project"],
        ]
