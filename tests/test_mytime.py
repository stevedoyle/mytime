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


if __name__ == "__main__":
    unittest.main()
