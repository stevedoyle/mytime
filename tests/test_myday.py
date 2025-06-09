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
08:00 Breakfast
09:00 Work
12:00 Lunch
13:00 End
# Notes
Some notes here.
"""

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
            tmp.write(content)
            tmp_filename = tmp.name

        try:
            result = extract_time_section(tmp_filename)
            assert result == [
                "08:00 Breakfast",
                "09:00 Work",
                "12:00 Lunch",
                "13:00 End",
            ]
        finally:
            os.remove(tmp_filename)

    def test_extract_time_section_no_time_section(self):
        content = """# My Day

08:00 Breakfast
09:00 Work
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
            "08:00 Breakfast",
            "09:00 Work",
            "12:00 Lunch",
            "12:30",
            "13:00 End",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["12:00", "0:30", "Lunch"],
            ["12:30", "0:30", ""],
            ["13:00", "-", "End"],
        ]

    def test_parse_time_entries_with_wikilinks(self):
        time_lines = [
            "08:00 [[Breakfast]]",
            "09:00 [[Work|Office]]",
            "12:00 End",
        ]
        result = parse_time_entries(time_lines)
        assert result == [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["12:00", "-", "End"],
        ]

    def test_calculate_total_time(self):
        entries = [
            ["08:00", "1:00", "Email"],
            ["09:00", "3:00", "Work"],
            ["12:00", "1:00", "Lunch"],
            ["13:00", "-", "End"],
        ]
        # Should sum only durations that are not "-" and not "Break"
        total_hours, total_rem_minutes = calculate_total_time(entries)
        assert total_hours == 5
        assert total_rem_minutes == 0

    def test_calculate_total_time_with_break(self):
        entries = [
            ["08:00", "1:00", "Email"],
            ["09:00", "0:30", "Break"],
            ["09:30", "2:00", "Work"],
            ["11:30", "-", "End"],
        ]
        # Should skip the "Break" entry
        total_hours, total_rem_minutes = calculate_total_time(entries)
        assert total_hours == 3
        assert total_rem_minutes == 0

    def test_filter_entries_case_sensitive(self):
        entries = [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["12:00", "1:00", "Lunch"],
            ["13:00", "-", "End"],
        ]
        filtered = filter_entries(entries, "work", ignore_case=False)
        # Should not match "Work" because of case
        assert filtered == []

    def test_filter_entries_ignore_case(self):
        entries = [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["12:00", "1:00", "Lunch"],
            ["13:00", "-", "End"],
        ]
        filtered = filter_entries(entries, "work", ignore_case=True)
        # Should match "Work" because ignore_case=True
        assert filtered == [["09:00", "3:00", "Work"]]

    def test_ignore_entries(self):
        entries = [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["12:00", "1:00", "Lunch"],
            ["13:00", "-", "End"],
        ]
        # Ignore activities containing "Work"
        ignored = ignore_entries(entries, "Work", ignore_case=False)
        assert ignored == [
            ["08:00", "1:00", "Breakfast"],
            ["12:00", "1:00", "Lunch"],
            ["13:00", "-", "End"],
        ]

        # Ignore activities containing "lunch" (case-insensitive)
        ignored = ignore_entries(entries, "lunch", ignore_case=True)
        assert ignored == [
            ["08:00", "1:00", "Breakfast"],
            ["09:00", "3:00", "Work"],
            ["13:00", "-", "End"],
        ]

    def test_calculate_total_time_include_breaks(self):
        entries = [
            ["08:00", "1:00", "Email"],
            ["09:00", "0:30", "Break"],
            ["09:30", "2:00", "Work"],
            ["11:30", "-", "End"],
        ]
        # With include_breaks=True, "Break" entry should be included in total
        total_hours, total_rem_minutes = calculate_total_time(
            entries, include_breaks=True
        )
        assert total_hours == 3
        assert total_rem_minutes == 30
