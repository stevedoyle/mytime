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
        input = pd.DataFrame(
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
        areas, total = mt.getSummary(input, "Area")
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


if __name__ == "__main__":
    unittest.main()
