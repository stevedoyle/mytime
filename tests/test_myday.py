import tempfile
import os
from myday import (
    extract_time_section,
    parse_time_entries,
    calculate_total_time,
    filter_entries,
    ignore_entries,
    summarize_by_focus,
    validate_time_entries,
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

    def test_parse_multi_dash_project_codes(self):
        time_lines = [
            "08:00 - 09:00 T: #Project-ABC-XYZ Work on multi-dash project",
            "09:00 - 10:00 T: #Project-DEF-GHI-JKL Work on another multi-dash project",
            "10:00 - 11:00 T: #Managing-Sub-Task Management subtask with dashes",
            "11:00 - 12:00 T: #Team-Alpha-Beta Team task with dashes",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Task", "ABC-XYZ", "Work on multi-dash project"],
            [
                "09:00",
                "1:00",
                "Task",
                "DEF-GHI-JKL",
                "Work on another multi-dash project",
            ],
            [
                "10:00",
                "1:00",
                "Task",
                "Managing-Sub-Task",
                "Management subtask with dashes",
            ],
            ["11:00", "1:00", "Task", "Team-Alpha-Beta", "Team task with dashes"],
        ]

    def test_summarize_by_focus_basic(self):
        """Test basic functionality of summarize_by_focus with all focus types."""
        type_totals = {
            "Task": 120,  # Deep focus
            "Learning": 60,  # Deep focus
            "Meeting": 90,  # Meeting focus
            "Comms": 30,  # Shallow focus
            "Admin": 45,  # Shallow focus
        }

        result = summarize_by_focus(type_totals)

        expected = {
            "Deep": 180,  # Task (120) + Learning (60)
            "Meeting": 90,  # Meeting (90)
            "Shallow": 75,  # Comms (30) + Admin (45)
        }

        assert result == expected

    def test_summarize_by_focus_empty_input(self):
        """Test summarize_by_focus with empty input."""
        type_totals = {}
        result = summarize_by_focus(type_totals)
        assert result == {}

    def test_summarize_by_focus_single_type(self):
        """Test summarize_by_focus with only one type."""
        type_totals = {"Task": 240}
        result = summarize_by_focus(type_totals)
        assert result == {"Deep": 240}

    def test_summarize_by_focus_missing_categories(self):
        """Test summarize_by_focus with missing categories."""
        # Only Deep focus activities
        type_totals = {"Task": 120, "Learning": 60}
        result = summarize_by_focus(type_totals)
        assert result == {"Deep": 180}

        # Only Meeting focus activities
        type_totals = {"Meeting": 90}
        result = summarize_by_focus(type_totals)
        assert result == {"Meeting": 90}

        # Only Shallow focus activities
        type_totals = {"Comms": 30, "Admin": 45}
        result = summarize_by_focus(type_totals)
        assert result == {"Shallow": 75}

    def test_summarize_by_focus_unknown_type(self):
        """Test summarize_by_focus with unknown activity type."""
        type_totals = {
            "Task": 120,
            "UnknownType": 60,  # This should not be categorized
            "Meeting": 90,
        }
        result = summarize_by_focus(type_totals)
        # Unknown types should be ignored
        assert result == {"Deep": 120, "Meeting": 90}

    def test_summarize_by_focus_zero_values(self):
        """Test summarize_by_focus with zero values."""
        type_totals = {
            "Task": 0,
            "Learning": 120,
            "Meeting": 0,
            "Comms": 30,
            "Admin": 0,
        }
        result = summarize_by_focus(type_totals)
        assert result == {"Deep": 120, "Meeting": 0, "Shallow": 30}

    def test_summarize_by_focus_break_type(self):
        """Test summarize_by_focus with Break type (should be ignored)."""
        type_totals = {
            "Task": 120,
            "Break": 60,  # Breaks are not categorized in focus
            "Meeting": 90,
        }
        result = summarize_by_focus(type_totals)
        # Break should not appear in any focus category
        assert result == {"Deep": 120, "Meeting": 90}

    def test_validate_time_entries_valid(self):
        """Test validation with valid time entries."""
        time_lines = [
            "08:00 - 09:00 T: #General Valid task",
            "09:00 - 10:30 M: #Team Meeting",
            "10:30 - 12:00 T: #Project-Work Work on project",
        ]
        errors = validate_time_entries(time_lines)
        assert errors == []

    def test_validate_time_entries_invalid_format(self):
        """Test validation with invalid format."""
        time_lines = [
            "08:00 - 09:00 T: #General Valid task",
            "invalid format line",
            "09:00 - 10:00 T: #Project-Work Work on project",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) >= 1
        assert any("Invalid format" in error for error in errors)
        assert any("Line 2" in error for error in errors)

    def test_validate_time_entries_invalid_type_code(self):
        """Test validation with invalid type code."""
        time_lines = [
            "08:00 - 09:00 T: #General Valid task",
            "09:00 - 10:00 X: #Team Invalid type",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1
        assert "Invalid type code 'X'" in errors[0]

    def test_validate_time_entries_end_before_start(self):
        """Test validation with end time before start time."""
        time_lines = [
            "08:00 - 09:00 T: #General Valid task",
            "13:00 - 12:00 T: #General End before start",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1
        assert "End time '12:00' should be after start time '13:00'" in errors[0]

    def test_validate_time_entries_overlapping(self):
        """Test validation with overlapping time blocks."""
        time_lines = [
            "08:00 - 09:00 T: #General Task 1",
            "08:30 - 09:30 T: #General Task 2 overlapping",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1
        assert "Overlapping time blocks" in errors[0]

    def test_validate_time_entries_gap(self):
        """Test validation with gap between time blocks."""
        time_lines = [
            "08:00 - 09:00 T: #General Task 1",
            "09:30 - 10:30 T: #General Task 2 with gap",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1
        assert "Gap of 30 minutes" in errors[0]

    def test_validate_time_entries_midnight_crossing(self):
        """Test validation with midnight crossing entries."""
        time_lines = [
            "23:00 - 01:00 T: #General Late night task",
            "01:00 - 02:00 T: #General Early morning task",
        ]
        errors = validate_time_entries(time_lines)
        assert errors == []  # Should be valid

    def test_validate_time_entries_empty_format(self):
        """Test validation with empty time block format (HH:MM - HH:MM)."""
        time_lines = [
            "08:00 - 09:00 T: #General Task with description",
            "09:00 - 10:00",  # Empty time block
            "10:00 - 11:00 M: #Team Meeting",
            "11:00 - 12:00",  # Another empty time block
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 0  # Should be no errors

    def test_validate_time_entries_mixed_format(self):
        """Test validation with mixed empty and full format."""
        time_lines = [
            "08:00 - 09:00 T: #General Task",
            "09:00 - 10:00",  # Empty time block
            "10:30 - 11:00 M: #Team Meeting",  # Gap from previous
            "11:00 - 12:00",  # Empty time block
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1  # Should only have gap error
        assert "Gap of 30 minutes" in errors[0]
        assert "Lines 2-3" in errors[0]

    def test_validate_time_entries_empty_format_invalid_time(self):
        """Test validation with empty format but invalid time."""
        time_lines = [
            "08:00 - 09:00",  # Valid empty
            "25:00 - 26:00",  # Invalid time in empty format
            "10:00 - 11:00 T: #General Task",
        ]
        errors = validate_time_entries(time_lines)
        assert len(errors) == 1
        assert "Invalid time format" in errors[0]
        assert "Line 2" in errors[0]
