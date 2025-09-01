import unittest
from unittest.mock import patch, mock_open
import mytime as mt
import pandas as pd
import pendulum


class TestMyTime(unittest.TestCase):
    def test_get_dates_today(self):
        start, end = mt.get_dates_today()
        expected_start = pendulum.today().to_date_string()
        expected_end = pendulum.today().to_date_string()
        self.assertEqual(start, expected_start, "Incorrect start date")
        self.assertEqual(end, expected_end, "Incorrect end date")

    def test_get_dates_thisweek(self):
        start, end = mt.get_dates_thisweek()
        expected_start = pendulum.today().start_of("week").to_date_string()
        expected_end = pendulum.today().end_of("week").to_date_string()
        self.assertEqual(start, expected_start, "Incorrect start date")
        self.assertEqual(end, expected_end, "Incorrect end date")

    def test_get_dates_lastweek(self):
        start, end = mt.get_dates_lastweek()
        expected_start = (
            pendulum.today().subtract(weeks=1).start_of("week").to_date_string()
        )
        expected_end = (
            pendulum.today().subtract(weeks=1).end_of("week").to_date_string()
        )
        self.assertEqual(start, expected_start, "Incorrect start date")
        self.assertEqual(end, expected_end, "Incorrect end date")

    def test_get_dates_thisquarter(self):
        start, end = mt.get_dates_thisquarter()
        expected_start = pendulum.today().first_of("quarter").to_date_string()
        expected_end = pendulum.today().last_of("quarter").to_date_string()
        self.assertEqual(start, expected_start, "Incorrect start date")
        self.assertEqual(end, expected_end, "Incorrect end date")

    def test_area_parsing(self):
        time_str = r"""
            Time.Area.Managing: 4.5
            Time.Area.Sample: 2.5
            Time.Area.Test: 1
            Time.Area.Collab: 0.5
            Time.Area.Collab.Meeting: 3
        """
        parsed = mt.extractTimeData(time_str)
        self.assertIn(["Area", "Managing", 4.5, False], parsed)
        self.assertIn(["Area", "Sample", 2.5, False], parsed)
        self.assertIn(["Area", "Test", 1, False], parsed)
        self.assertIn(["Area", "Collab", 0.5, False], parsed)
        self.assertIn(["Area", "Collab.Meeting", 3, False], parsed)

    def test_area_parsing_failure(self):
        self.assertEqual(mt.extractTimeData(""), [])
        self.assertEqual(mt.extractTimeData("Time.Area.Managing: "), [])

        time_str = r"""
            Time.Area.Managing: 4.5
            Tim.Area.Sample: 2.5
        """
        self.assertEqual(
            mt.extractTimeData(time_str), [["Area", "Managing", 4.5, False]]
        )

    def test_timedata_parsing(self):
        time_str = r"""
            Time.Overhead.Managing: 4.5
            Time.Proj.Sample: 2.5
            Time.Proj.Test: 1
            Time.Area.Collab: 0.5
            Time.Area.Collab.Meeting: 3
        """
        parsed = mt.extractTimeData(time_str)
        self.assertIn(["Overhead", "Managing", 4.5, False], parsed)
        self.assertIn(["Proj", "Sample", 2.5, False], parsed)
        self.assertIn(["Proj", "Test", 1, False], parsed)
        self.assertIn(["Area", "Collab", 0.5, False], parsed)
        self.assertIn(["Area", "Collab.Meeting", 3, False], parsed)

    def test_timedata_parsing_with_prefix(self):
        time_str = r"""
            Time.Overhead.Managing: 4.5
            Time.Proj.Sample: 2.5
            Time.Proj.Test: 1
            Time.Area.Collab: 0.5
            Time.Area.Collab.Meeting: 3
        """
        parsed = mt.extractTimeData(time_str, prefix="Prefix")
        self.assertIn(["Prefix", "Overhead", "Managing", 4.5, False], parsed)
        self.assertIn(["Prefix", "Proj", "Sample", 2.5, False], parsed)
        self.assertIn(["Prefix", "Proj", "Test", 1, False], parsed)
        self.assertIn(["Prefix", "Area", "Collab", 0.5, False], parsed)
        self.assertIn(["Prefix", "Area", "Collab.Meeting", 3, False], parsed)

    def test_getAreaSummary(self):
        df_input = pd.DataFrame(
            [
                ("Area", "Managing", 3.5),
                ("Area", "Sample", 1),
                ("Area", "Sample", 1.5),
                ("Area", "Managing", 2),
            ],
            columns=["Category", "Name", "Hours"],
        )
        expected = pd.DataFrame(
            [("Managing", 5.5, 68.75), ("Sample", 2.5, 31.25)],
            columns=["Name", "Hours", "%"],
        )
        expected_total = 8.0
        areas, total = mt.getSummary(df_input, "Area")
        self.assertEqual(areas.values.tolist(), expected.values.tolist())
        self.assertEqual(total, expected_total)

    def test_gettimedata(self):
        mock_content = """
            Time.Area.Managing: 1
            Time.Area.Collab.Meetings: 3
            Time.Area.Collab.Email: 2
            Time.Area.DeepWork: 4"""
        expected = [
            ["2023-10-16", "Area", "Managing", 1.0, False],
            ["2023-10-16", "Area", "Collab.Meetings", 3.0, False],
            ["2023-10-16", "Area", "Collab.Email", 2.0, False],
            ["2023-10-16", "Area", "DeepWork", 4.0, False],
        ]

        with patch("builtins.open", new=mock_open(read_data=mock_content)) as mock_file:
            fname = "./2023-10-16.md"
            td = mt.gettimedata([fname])
            mock_file.assert_called_with("./2023-10-16.md", encoding="UTF-8")
            self.assertEqual(len(td), 4)
            self.assertEqual(td.values.tolist(), expected)

    @patch("builtins.open", new_callable=mock_open)
    def test_gettimedata_multifile(self, mo):
        mock_f1 = """
            Time.Area.Managing: 1
            Time.Area.Collab.Meetings: 3
            Time.Area.Collab.Email: 2
            Time.Area.DeepWork: 4"""
        mock_f2 = """
            Time.Area.Managing: 2
            Time.Area.Collab.Meetings: 2.5
            Time.Area.Collab.Email: 1.5
            Time.Area.DeepWork: 3"""
        expected = [
            ["2023-10-16", "Area", "Managing", 1.0, False],
            ["2023-10-16", "Area", "Collab.Meetings", 3.0, False],
            ["2023-10-16", "Area", "Collab.Email", 2.0, False],
            ["2023-10-16", "Area", "DeepWork", 4.0, False],
            ["2023-10-17", "Area", "Managing", 2.0, False],
            ["2023-10-17", "Area", "Collab.Meetings", 2.5, False],
            ["2023-10-17", "Area", "Collab.Email", 1.5, False],
            ["2023-10-17", "Area", "DeepWork", 3, False],
        ]

        f1name = "2023-10-16.md"
        f2name = "2023-10-17.md"
        handlers = (
            mock_open(read_data=mock_f1).return_value,
            mock_open(read_data=mock_f2).return_value,
        )
        mo.side_effect = handlers
        td = mt.gettimedata([f1name, f2name])
        self.assertEqual(len(td), 8)
        self.assertEqual(td.values.tolist(), expected)

    def test_onsite(self):
        mock_content = """
            "onsite: true",
            Time.Area.Managing: 1"""

        parsed = mt.extractTimeData(mock_content)
        self.assertIn(["Area", "Managing", 1, True], parsed)

        mock_content = """
            Time.Area.Managing: 1"""

        parsed = mt.extractTimeData(mock_content)
        self.assertIn(["Area", "Managing", 1, False], parsed)

    def test_extractTimeBlocks(self):
        mock_content = """# Daily Note

## Time

09:00 - 11:00 T: #Project-Example1 Development work
11:00 - 12:00 M: #Team Weekly meeting
14:00 - 16:00 T: #General Bug fixes

## Other Section"""

        time_blocks = mt.extractTimeBlocks(mock_content)
        expected = [
            "09:00 - 11:00 T: #Project-Example1 Development work",
            "11:00 - 12:00 M: #Team Weekly meeting",
            "14:00 - 16:00 T: #General Bug fixes",
        ]
        self.assertEqual(time_blocks, expected)

    def test_extractTimeBlocks_empty(self):
        mock_content = """# Daily Note

No time section"""
        time_blocks = mt.extractTimeBlocks(mock_content)
        self.assertEqual(time_blocks, [])

    def test_parseTimeBlocks(self):
        time_blocks = [
            "09:00 - 11:00 T: #Project-Example1 Development work",
            "11:00 - 12:00 M: #Team Weekly meeting",
            "14:00 - 16:00 T: #General Bug fixes",
            "16:00 - 17:00 B: #General Break time",
        ]

        tasks_by_project = mt.parseTimeBlocks(time_blocks)

        # Check that Break is not included
        self.assertNotIn(
            "General",
            [
                task["type"]
                for project_tasks in tasks_by_project.values()
                for task in project_tasks
                if task["type"] == "Break"
            ],
        )

        # Check Example1 project
        self.assertIn("Example1", tasks_by_project)
        example1_tasks = tasks_by_project["Example1"]
        self.assertEqual(len(example1_tasks), 1)
        self.assertEqual(example1_tasks[0]["type"], "Task")
        self.assertEqual(example1_tasks[0]["description"], "Development work")
        self.assertEqual(example1_tasks[0]["duration"], "2:00")

        # Check Team project
        self.assertIn("Team", tasks_by_project)
        team_tasks = tasks_by_project["Team"]
        self.assertEqual(len(team_tasks), 1)
        self.assertEqual(team_tasks[0]["type"], "Meeting")
        self.assertEqual(team_tasks[0]["description"], "Weekly meeting")
        self.assertEqual(team_tasks[0]["duration"], "1:00")

        # Check General project
        self.assertIn("General", tasks_by_project)
        general_tasks = tasks_by_project["General"]
        self.assertEqual(len(general_tasks), 1)
        self.assertEqual(general_tasks[0]["type"], "Task")
        self.assertEqual(general_tasks[0]["description"], "Bug fixes")

    def test_parseTimeBlocks_complex_project_tags(self):
        """Test parsing of complex project tags that include dots, underscores, etc."""
        time_blocks = [
            "09:00 - 10:00 T: #Project.Mobile.v2 App development",
            "10:00 - 11:00 T: #Bug_123 Critical bug fix",
            "11:00 - 12:00 M: #Client-ABC.Project Status meeting",
            "13:00 - 14:00 T: No project tag here",
            "14:00 - 15:00 A: #Project-Test.v2_beta Testing phase",
        ]

        tasks_by_project = mt.parseTimeBlocks(time_blocks)

        # Check Project.Mobile.v2 project (should preserve dots)
        self.assertIn("Project.Mobile.v2", tasks_by_project)
        mobile_tasks = tasks_by_project["Project.Mobile.v2"]
        self.assertEqual(len(mobile_tasks), 1)
        self.assertEqual(mobile_tasks[0]["description"], "App development")

        # Check Bug_123 project (should preserve underscores)
        self.assertIn("Bug_123", tasks_by_project)
        bug_tasks = tasks_by_project["Bug_123"]
        self.assertEqual(len(bug_tasks), 1)
        self.assertEqual(bug_tasks[0]["description"], "Critical bug fix")

        # Check Client-ABC.Project (should continue until whitespace)
        self.assertIn("Client-ABC.Project", tasks_by_project)
        client_tasks = tasks_by_project["Client-ABC.Project"]
        self.assertEqual(len(client_tasks), 1)
        self.assertEqual(client_tasks[0]["description"], "Status meeting")

        # Check General project (no tag should default to General)
        self.assertIn("General", tasks_by_project)
        general_tasks = tasks_by_project["General"]
        self.assertEqual(len(general_tasks), 1)
        self.assertEqual(general_tasks[0]["description"], "No project tag here")

        # Check Project-Test.v2_beta (Project- prefix should be stripped, rest preserved)
        self.assertIn("Test.v2_beta", tasks_by_project)
        test_tasks = tasks_by_project["Test.v2_beta"]
        self.assertEqual(len(test_tasks), 1)
        self.assertEqual(test_tasks[0]["description"], "Testing phase")

    def test_getTimeBlockData(self):
        mock_content = """## Time

09:00 - 11:00 T: #Project-Example1 Development work
11:00 - 12:00 M: #Team Weekly meeting"""

        with patch("builtins.open", new=mock_open(read_data=mock_content)) as mock_file:
            fname = "./2023-10-16.md"
            tasks_by_project = mt.getTimeBlockData([fname])
            mock_file.assert_called_with("./2023-10-16.md", encoding="UTF-8")

            self.assertEqual(len(tasks_by_project), 2)
            self.assertIn("Example1", tasks_by_project)
            self.assertIn("Team", tasks_by_project)

            # Check Example1 tasks
            example1_tasks = tasks_by_project["Example1"]
            self.assertEqual(len(example1_tasks), 1)
            self.assertEqual(example1_tasks[0]["date"], "2023-10-16")
            self.assertEqual(example1_tasks[0]["type"], "Task")
            self.assertEqual(example1_tasks[0]["description"], "Development work")

            # Check Team tasks
            team_tasks = tasks_by_project["Team"]
            self.assertEqual(len(team_tasks), 1)
            self.assertEqual(team_tasks[0]["date"], "2023-10-16")
            self.assertEqual(team_tasks[0]["type"], "Meeting")
            self.assertEqual(team_tasks[0]["description"], "Weekly meeting")

    def test_extractNotes(self):
        mock_content = """# Daily Note

## Time

09:00 - 11:00 T: #Project-Example1 Development work

## Notes

Great progress on the project today. Fixed several bugs.

Key achievements:
- Resolved authentication issue
- Completed dashboard feature

## Tomorrow

- Continue with testing
- Team meeting"""

        notes = mt.extractNotes(mock_content)
        expected = [
            "Great progress on the project today. Fixed several bugs.",
            "",
            "Key achievements:",
            "- Resolved authentication issue",
            "- Completed dashboard feature",
        ]
        self.assertEqual(notes, expected)

    def test_extractNotes_empty(self):
        mock_content = """# Daily Note

## Time

09:00 - 11:00 T: #Project-Example1 Development work

## Tomorrow

- Continue with testing"""

        notes = mt.extractNotes(mock_content)
        self.assertEqual(notes, [])

    def test_extractNotes_no_section(self):
        mock_content = """# Daily Note

## Time

09:00 - 11:00 T: #Project-Example1 Development work"""

        notes = mt.extractNotes(mock_content)
        self.assertEqual(notes, [])

    def test_extractNotes_empty_section(self):
        mock_content = """# Daily Note

## Notes

## Tomorrow

- Continue with testing"""

        notes = mt.extractNotes(mock_content)
        self.assertEqual(notes, [])

    def test_extractNotes_whitespace_handling(self):
        mock_content = """# Daily Note

## Notes


Great day with meaningful progress.


Key points:
- Fixed bug #123
- Meeting was productive


## Tomorrow

- Continue"""

        notes = mt.extractNotes(mock_content)
        expected = [
            "Great day with meaningful progress.",
            "",
            "",
            "Key points:",
            "- Fixed bug #123",
            "- Meeting was productive",
        ]
        self.assertEqual(notes, expected)

    def test_getNotesData(self):
        mock_content1 = """## Notes

Good progress today. Fixed authentication bug."""

        mock_content2 = """## Notes

Completed dashboard feature.
Very productive day."""

        with patch(
            "builtins.open",
            side_effect=[
                mock_open(read_data=mock_content1).return_value,
                mock_open(read_data=mock_content2).return_value,
            ],
        ):
            files = ["2023-10-15.md", "2023-10-16.md"]
            notes_data = mt.getNotesData(files)

            self.assertEqual(len(notes_data), 2)
            self.assertIn("2023-10-15", notes_data)
            self.assertIn("2023-10-16", notes_data)

            self.assertEqual(
                notes_data["2023-10-15"],
                ["Good progress today. Fixed authentication bug."],
            )
            self.assertEqual(
                notes_data["2023-10-16"],
                ["Completed dashboard feature.", "Very productive day."],
            )

    def test_getNotesData_mixed_files(self):
        mock_content_with_notes = """## Notes

Important note from this day."""

        mock_content_without_notes = """## Time

09:00 - 10:00 T: #Project Work

## Tomorrow

- Continue tomorrow"""

        with patch(
            "builtins.open",
            side_effect=[
                mock_open(read_data=mock_content_with_notes).return_value,
                mock_open(read_data=mock_content_without_notes).return_value,
            ],
        ):
            files = ["2023-10-15.md", "2023-10-16.md"]
            notes_data = mt.getNotesData(files)

            # Only files with notes should be included
            self.assertEqual(len(notes_data), 1)
            self.assertIn("2023-10-15", notes_data)
            self.assertNotIn("2023-10-16", notes_data)


if __name__ == "__main__":
    unittest.main()
