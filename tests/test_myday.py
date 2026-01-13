import tempfile
import os
from myday import (
    extract_time_section,
    extract_time_section_for_validation,
    parse_time_entries,
    calculate_total_time,
    filter_entries,
    ignore_entries,
    summarize_by_focus,
    validate_time_entries,
    fix_time_gaps,
    fix_missing_colons,
)


def test_extract_time_section_basic():
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


def test_extract_time_section_no_time_section():
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


def test_parse_time_entries_basic():
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


def test_parse_time_entries_with_no_project():
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


def test_calculate_total_time():
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


def test_calculate_total_time_with_break():
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


def test_filter_entries_case_sensitive():
    entries = [
        ["08:00", "1:00", "Task", "General", "Breakfast"],
        ["09:00", "3:00", "Task", "Work", "Work on project"],
        ["12:00", "1:00", "Break", "General", "Lunch"],
        ["13:00", "-", "Meeting", "Team", "Meeting"],
    ]
    filtered = filter_entries(entries, "work", ignore_case=False)
    # Should not match "Work on project" because of case
    assert filtered == []


def test_filter_entries_ignore_case():
    entries = [
        ["08:00", "1:00", "Task", "General", "Breakfast"],
        ["09:00", "3:00", "Task", "Work", "Work on project"],
        ["12:00", "1:00", "Break", "General", "Lunch"],
        ["13:00", "-", "Meeting", "Team", "Meeting"],
    ]
    filtered = filter_entries(entries, "work", ignore_case=True)
    # Should match "Work on project" because ignore_case=True
    assert filtered == [["09:00", "3:00", "Task", "Work", "Work on project"]]


def test_ignore_entries():
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


def test_calculate_total_time_include_breaks():
    entries = [
        ["08:00", "1:00", "Task", "General", "Email"],
        ["09:00", "0:30", "Break", "General", "Coffee break"],
        ["09:30", "2:00", "Task", "Work", "Work on project"],
        ["11:30", "-", "Meeting", "Team", "Meeting"],
    ]
    # With include_breaks=True, "Break" entry should be included in total
    total_hours, total_rem_minutes = calculate_total_time(entries, include_breaks=True)
    assert total_hours == 3
    assert total_rem_minutes == 30


def test_ignore_empty():
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


def test_parse_project_codes():
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


def test_parse_multi_dash_project_codes():
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


def test_summarize_by_focus_basic():
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


def test_summarize_by_focus_empty_input():
    """Test summarize_by_focus with empty input."""
    type_totals = {}
    result = summarize_by_focus(type_totals)
    assert result == {}


def test_summarize_by_focus_single_type():
    """Test summarize_by_focus with only one type."""
    type_totals = {"Task": 240}
    result = summarize_by_focus(type_totals)
    assert result == {"Deep": 240}


def test_summarize_by_focus_missing_categories():
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


def test_summarize_by_focus_unknown_type():
    """Test summarize_by_focus with unknown activity type."""
    type_totals = {
        "Task": 120,
        "UnknownType": 60,  # This should not be categorized
        "Meeting": 90,
    }
    result = summarize_by_focus(type_totals)
    # Unknown types should be ignored
    assert result == {"Deep": 120, "Meeting": 90}


def test_summarize_by_focus_zero_values():
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


def test_summarize_by_focus_break_type():
    """Test summarize_by_focus with Break type (should be ignored)."""
    type_totals = {
        "Task": 120,
        "Break": 60,  # Breaks are not categorized in focus
        "Meeting": 90,
    }
    result = summarize_by_focus(type_totals)
    # Break should not appear in any focus category
    assert result == {"Deep": 120, "Meeting": 90}


def test_validate_time_entries_valid():
    """Test validation with valid time entries."""
    time_lines = [
        "08:00 - 09:00 T: #General Valid task",
        "09:00 - 10:30 M: #Team Meeting",
        "10:30 - 12:00 T: #Project-Work Work on project",
    ]
    errors = validate_time_entries(time_lines)
    assert errors == []


def test_validate_time_entries_invalid_format():
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


def test_validate_time_entries_invalid_type_code():
    """Test validation with invalid type code."""
    time_lines = [
        "08:00 - 09:00 T: #General Valid task",
        "09:00 - 10:00 X: #Team Invalid type",
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 1
    assert "Invalid type code 'X'" in errors[0]


def test_validate_time_entries_end_before_start():
    """Test validation with end time before start time."""
    time_lines = [
        "08:00 - 09:00 T: #General Valid task",
        "13:00 - 12:00 T: #General End before start",
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 1
    assert "End time '12:00' should be after start time '13:00'" in errors[0]


def test_validate_time_entries_overlapping():
    """Test validation with overlapping time blocks."""
    time_lines = [
        "08:00 - 09:00 T: #General Task 1",
        "08:30 - 09:30 T: #General Task 2 overlapping",
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 1
    assert "Overlapping time blocks" in errors[0]


def test_validate_time_entries_gap():
    """Test validation with gap between time blocks."""
    time_lines = [
        "08:00 - 09:00 T: #General Task 1",
        "09:30 - 10:30 T: #General Task 2 with gap",
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 1
    assert "Gap of 30 minutes" in errors[0]


def test_validate_time_entries_midnight_crossing():
    """Test validation with midnight crossing entries."""
    time_lines = [
        "23:00 - 01:00 T: #General Late night task",
        "01:00 - 02:00 T: #General Early morning task",
    ]
    errors = validate_time_entries(time_lines)
    assert errors == []  # Should be valid


def test_validate_time_entries_empty_format():
    """Test validation with empty time block format (HH:MM - HH:MM)."""
    time_lines = [
        "08:00 - 09:00 T: #General Task with description",
        "09:00 - 10:00",  # Empty time block
        "10:00 - 11:00 M: #Team Meeting",
        "11:00 - 12:00",  # Another empty time block
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 0  # Should be no errors


def test_validate_time_entries_mixed_format():
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


def test_validate_time_entries_empty_format_invalid_time():
    """Test validation with empty format but invalid time."""
    time_lines = [
        "25:00 - 26:00",  # Invalid time in empty format
    ]
    errors = validate_time_entries(time_lines)
    assert len(errors) == 1
    assert "Invalid time format" in errors[0]
    assert "Line 1" in errors[0]


"""Test cases for the fix_time_gaps function."""


def test_fix_time_gaps_single_gap():
    """Test fixing a single time gap."""
    content = """# My Day

## Time
09:00 - 10:00 T: #General Morning task
10:30 - 11:30 T: #General Later task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        # Get validation lines
        validation_lines = extract_time_section_for_validation(tmp_filename)

        # Fix the gaps
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True  # Should have made fixes

        # Verify the file was updated
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # The first entry should now end at 10:30
        assert "09:00 - 10:30 T: #General Morning task" in updated_content
        assert "10:30 - 11:30 T: #General Later task" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_multiple_gaps():
    """Test fixing multiple time gaps."""
    content = """# My Day

## Time
08:00 - 09:00 T: #General First task
09:30 - 10:00 T: #General Second task
10:15 - 11:00 T: #General Third task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        # Verify multiple fixes were applied
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "08:00 - 09:30 T: #General First task" in updated_content
        assert "09:30 - 10:15 T: #General Second task" in updated_content
        assert "10:15 - 11:00 T: #General Third task" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_empty_format():
    """Test fixing gaps with empty time format entries."""
    content = """# My Day

## Time
09:00 - 10:00
10:30 - 11:30

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "09:00 - 10:30" in updated_content
        assert "10:30 - 11:30" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_mixed_format():
    """Test fixing gaps with mixed empty and full format entries."""
    content = """# My Day

## Time
09:00 - 10:00
10:15 - 11:00 T: #General Task with description
11:30 - 12:00

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # First gap: 09:00-10:00 should extend to 10:15
        assert "09:00 - 10:15" in updated_content
        # Second gap: 10:15-11:00 should extend to 11:30
        assert "10:15 - 11:30 T: #General Task with description" in updated_content
        # Third entry unchanged
        assert "11:30 - 12:00" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_no_gaps():
    """Test fix function when there are no gaps."""
    content = """# My Day

## Time
09:00 - 10:00 T: #General First task
10:00 - 11:00 T: #General Second task
11:00 - 12:00 T: #General Third task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is False  # No fixes should be made

        # Content should remain unchanged
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert updated_content == content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_overlapping_entries():
    """Test fix function when there are overlapping entries (should not fix these)."""
    content = """# My Day

## Time
09:00 - 11:00 T: #General First task
10:30 - 12:00 T: #General Overlapping task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is False  # No gaps to fix (has overlap instead)

        # Content should remain unchanged
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert updated_content == content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_unordered_entries():
    """Test fixing gaps when entries are not in chronological order."""
    content = """# My Day

## Time
08:00 - 09:00 T: #General Morning task
09:30 - 10:30 T: #General Later task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # The first task should extend to 09:30
        assert "08:00 - 09:30 T: #General Morning task" in updated_content
        assert "09:30 - 10:30 T: #General Later task" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_actual_midnight_crossing():
    """Test with valid midnight crossing that should NOT be fixed."""
    content = """# My Day

## Time
23:00 - 01:00 T: #General Late task crossing midnight
01:00 - 02:00 T: #General Early task

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is False  # Should not need fixing - no gap

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Content should remain unchanged
        assert updated_content == content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_preserves_other_sections():
    """Test that fixing gaps preserves other sections of the file."""
    content = """# My Day

Some intro text here.

## Goals
- Goal 1
- Goal 2

## Time
09:00 - 10:00 T: #General Morning task
10:30 - 11:30 T: #General Later task

## Notes
Some important notes.

## Reflection
Today was good.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Check that other sections are preserved
        assert "Some intro text here." in updated_content
        assert "## Goals" in updated_content
        assert "- Goal 1" in updated_content
        assert "## Notes" in updated_content
        assert "Some important notes." in updated_content
        assert "## Reflection" in updated_content
        assert "Today was good." in updated_content

        # Check that the time gap was fixed
        assert "09:00 - 10:30 T: #General Morning task" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_invalid_entries_ignored():
    """Test that invalid entries are ignored during fixing."""
    content = """# My Day

## Time
09:00 - 10:00 T: #General Valid task
Invalid line here
10:30 - 11:30 T: #General Another valid task
Another invalid line

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # The gap should be fixed
        assert "09:00 - 10:30 T: #General Valid task" in updated_content
        assert "10:30 - 11:30 T: #General Another valid task" in updated_content

        # Invalid lines should remain unchanged
        assert "Invalid line here" in updated_content
        assert "Another invalid line" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_edge_cases():
    """Test fix function with various edge cases."""
    content = """# My Day

## Time
09:00 - 09:00 T: #General Zero duration task
09:15 - 10:00 T: #General Regular task
10:30 - 11:00 T: #General Task with gap

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Only the gap between 10:00 and 10:30 should be fixed
        # Zero duration task may remain as is (depending on validation logic)
        assert "09:15 - 10:30 T: #General Regular task" in updated_content
        assert "10:30 - 11:00 T: #General Task with gap" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_time_gaps_no_time_section():
    """Test fix function with a file that has no time section."""
    content = """# My Day

Some content but no time section.

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        validation_lines = extract_time_section_for_validation(tmp_filename)
        result = fix_time_gaps(tmp_filename, validation_lines)
        assert result is False  # No time section = no gaps to fix

        # Content should remain unchanged
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert updated_content == content

    finally:
        os.remove(tmp_filename)


# Test cases for the fix_missing_colons function.


def test_fix_missing_colons_single_entry():
    """Test fixing a single entry with missing colon."""
    content = """# My Day

## Time
19:00 - 20:00 M #Managing Stuff

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        # Fix missing colons
        result = fix_missing_colons(tmp_filename)
        assert result is True  # Should have made fixes

        # Verify the file was updated
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # The colon should be added after M
        assert "19:00 - 20:00 M: #Managing Stuff" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_multiple_entries():
    """Test fixing multiple entries with missing colons."""
    content = """# My Day

## Time
09:00 - 10:00 T #General Morning work
10:00 - 11:00 M #Team Meeting
11:00 - 12:00 C #General Email
12:00 - 13:00 B #General Lunch

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is True

        # Verify all colons were added
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "09:00 - 10:00 T: #General Morning work" in updated_content
        assert "10:00 - 11:00 M: #Team Meeting" in updated_content
        assert "11:00 - 12:00 C: #General Email" in updated_content
        assert "12:00 - 13:00 B: #General Lunch" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_mixed_format():
    """Test fixing entries where some have colons and some don't."""
    content = """# My Day

## Time
09:00 - 10:00 T: #General Already has colon
10:00 - 11:00 M #Team Missing colon
11:00 - 12:00 T: #Project-Work Another with colon
12:00 - 13:00 A #General Another missing

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is True

        # Verify only the missing colons were added
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "09:00 - 10:00 T: #General Already has colon" in updated_content
        assert "10:00 - 11:00 M: #Team Missing colon" in updated_content
        assert "11:00 - 12:00 T: #Project-Work Another with colon" in updated_content
        assert "12:00 - 13:00 A: #General Another missing" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_no_missing():
    """Test fix function when all entries already have colons."""
    content = """# My Day

## Time
09:00 - 10:00 T: #General Morning task
10:00 - 11:00 M: #Team Meeting
11:00 - 12:00 T: #Project-Work Work on project

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is False  # No fixes should be made

        # Content should remain unchanged
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert updated_content == content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_with_description():
    """Test fixing entries with various description formats."""
    content = """# My Day

## Time
09:00 - 10:00 T Description without hashtag
10:00 - 11:00 M #Project-Work Work on feature
11:00 - 12:00 L #Team-Learning Learning session

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "09:00 - 10:00 T: Description without hashtag" in updated_content
        assert "10:00 - 11:00 M: #Project-Work Work on feature" in updated_content
        assert "11:00 - 12:00 L: #Team-Learning Learning session" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_preserves_other_sections():
    """Test that fixing colons preserves other sections of the file."""
    content = """# My Day

Some intro text here.

## Goals
- Goal 1
- Goal 2

## Time
09:00 - 10:00 T #General Morning task
10:00 - 11:00 M #Team Meeting

## Notes
Some important notes.

## Reflection
Today was good.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Check that other sections are preserved
        assert "Some intro text here." in updated_content
        assert "## Goals" in updated_content
        assert "- Goal 1" in updated_content
        assert "## Notes" in updated_content
        assert "Some important notes." in updated_content
        assert "## Reflection" in updated_content
        assert "Today was good." in updated_content

        # Check that colons were added
        assert "09:00 - 10:00 T: #General Morning task" in updated_content
        assert "10:00 - 11:00 M: #Team Meeting" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_all_type_codes():
    """Test fixing all different type codes."""
    content = """# My Day

## Time
08:00 - 09:00 T #General Task
09:00 - 10:00 M #Team Meeting
10:00 - 11:00 C #General Communication
11:00 - 12:00 A #General Admin work
12:00 - 13:00 L #General Learning
13:00 - 14:00 B #General Break

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is True

        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "08:00 - 09:00 T: #General Task" in updated_content
        assert "09:00 - 10:00 M: #Team Meeting" in updated_content
        assert "10:00 - 11:00 C: #General Communication" in updated_content
        assert "11:00 - 12:00 A: #General Admin work" in updated_content
        assert "12:00 - 13:00 L: #General Learning" in updated_content
        assert "13:00 - 14:00 B: #General Break" in updated_content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_no_time_section():
    """Test fix function with a file that has no time section."""
    content = """# My Day

Some content but no time section.

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        result = fix_missing_colons(tmp_filename)
        assert result is False  # No time section = no fixes to make

        # Content should remain unchanged
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert updated_content == content

    finally:
        os.remove(tmp_filename)


def test_fix_missing_colons_integration_with_gaps():
    """Test that fixing colons works together with fixing gaps."""
    content = """# My Day

## Time
09:00 - 10:00 T #General First task
10:30 - 11:30 M #Team Second task with gap

## Notes
Some notes here.
"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_filename = tmp.name

    try:
        # First fix missing colons
        colons_fixed = fix_missing_colons(tmp_filename)
        assert colons_fixed is True

        # Then fix gaps
        validation_lines = extract_time_section_for_validation(tmp_filename)
        gaps_fixed = fix_time_gaps(tmp_filename, validation_lines)
        assert gaps_fixed is True

        # Verify both fixes were applied
        with open(tmp_filename, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Should have colon and extended end time
        assert "09:00 - 10:30 T: #General First task" in updated_content
        assert "10:30 - 11:30 M: #Team Second task with gap" in updated_content

    finally:
        os.remove(tmp_filename)
