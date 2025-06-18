# Script for summarizing time tracking information from daily notes.

from version import __version__
import os
import click
import dateutil
import logging
import pandas as pd
import pendulum
import re
import sys
from tabulate import tabulate


def extractTimeData(contents, prefix=""):
    td = []

    onsite = False
    onsite_pattern = r"onsite:\s*true"
    if re.search(onsite_pattern, contents):
        onsite = True

    pattern = r"Time\.(\w+)\.(.+):\s*(\d+\.?\d?)"
    mobj = re.findall(pattern, contents)
    for category, name, hours in mobj:
        if prefix:
            td.append([prefix, category, name, float(hours), onsite])
        else:
            td.append([category, name, float(hours), onsite])
    return td


def getSummary(df, category):
    areadf = df.loc[df["Category"] == category].drop(columns=["Category"])
    areadf = areadf.groupby("Name")["Hours"].sum().reset_index()
    areadf = areadf.sort_values(by=["Hours"], ascending=False)
    total = areadf["Hours"].sum()
    areadf["%"] = areadf["Hours"] / total * 100
    return areadf, total


def getFilesInRange(fpath, begin, end):
    begindate = dateutil.parser.parse(begin).date()
    enddate = dateutil.parser.parse(end).date()

    files = []
    with os.scandir(fpath) as it:
        for entry in it:
            if entry.name.endswith(".md") and entry.is_file():
                try:
                    filedate = dateutil.parser.parse(
                        os.path.basename(entry).split(".")[0]
                    ).date()
                    if (begindate <= filedate) and (filedate <= enddate):
                        files.append(entry.path)
                except dateutil.parser.ParserError:
                    continue
    return files


def gettimedata(files):
    timedata = []
    for entry in files:
        with open(entry, encoding="UTF-8") as f:
            name = os.path.splitext(os.path.basename(entry))[0]
            td = extractTimeData(f.read(), prefix=name)
            if len(td) > 0:
                timedata.extend(td)
    df = pd.DataFrame(
        timedata, columns=["Date", "Category", "Name", "Hours", "Onsite"]
    ).astype({"Hours": "float"})
    return df


def getNumDays(df):
    return df["Date"].nunique()


def printTable(table, tsv):
    tblFmt = "github"
    if tsv:
        tblFmt = "tsv"

    print(
        tabulate(
            table,
            headers="keys",
            showindex=False,
            floatfmt=("", ".1f", ".2f"),
            tablefmt=tblFmt,
        )
    )


def reportTimeSpent(path, categories, begin, end, tsv=False, onsite=False, brief=False):
    files = []

    if brief:
        categories = ["Focus"]
    else:
        categories = normalizeCategories(categories)

    try:
        files = getFilesInRange(path, begin, end)
        td = gettimedata(files)
        for category in categories:
            areas, total_hours = getSummary(td, category)
            days = getNumDays(td)
            if total_hours:
                if not brief:
                    printTable(areas, tsv)
                print()
                print(f"Total hours:       {total_hours: >6}")
                print(f"Total days:        {days: >6}")
                print(f"Average hours/day: {total_hours / days: >6.1f}")
                print()

        if days > 0 and onsite:
            onsite_days = getOnsiteDays(td)
            print(
                f"Total onsite days: {onsite_days: >6} ({(onsite_days / days * 100):.0f}%)"
            )
    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


def getOnsiteDays(df):
    onsite = df.loc[df["Onsite"]]
    return onsite["Date"].nunique()


def dumpTimeEntries(path, categories, begin, end):
    categories = normalizeCategories(categories)

    try:
        files = getFilesInRange(path, begin, end)
        td = gettimedata(files)
        td = filterTimeData(td, categories)
        td.to_csv(sys.stdout, index=False)
    except ValueError as err:
        print(f"Error parsing date: {err}")
        return


def filterTimeData(df, categories):
    return df[df["Category"].isin(categories)]


def normalizeCategories(categories):
    # Normalize category strings
    categories = [cat.title() for cat in categories]
    if "All" in categories:
        categories = ["Proj", "Area", "Focus", "Prof"]
    return categories


##########################################################################


def get_dates_today():
    today = pendulum.today().to_date_string()
    return today, today


def get_dates_yesterday():
    yesterday = pendulum.yesterday().to_date_string()
    return yesterday, yesterday


def get_dates_thisweek():
    today = pendulum.today()
    start = today.start_of("week").to_date_string()
    end = today.end_of("week").to_date_string()
    return start, end


def get_dates_lastweek():
    lastweek = pendulum.today().subtract(weeks=1)
    start = lastweek.start_of("week").to_date_string()
    end = lastweek.end_of("week").to_date_string()
    return start, end


def get_dates_thismonth():
    today = pendulum.today()
    start = today.start_of("month").to_date_string()
    end = today.end_of("month").to_date_string()
    return start, end


def get_dates_lastmonth():
    lastmonth = pendulum.today().subtract(months=1)
    start = lastmonth.start_of("month").to_date_string()
    end = lastmonth.end_of("month").to_date_string()
    return start, end


def get_dates_thisquarter():
    today = pendulum.today()
    start = today.first_of("quarter").to_date_string()
    end = today.last_of("quarter").to_date_string()
    return start, end


def get_dates_lastquarter():
    lastmonth = pendulum.today().subtract(months=3)
    start = lastmonth.first_of("quarter").to_date_string()
    end = lastmonth.last_of("quarter").to_date_string()
    return start, end


def get_dates_thisyear():
    today = pendulum.today()
    start = today.start_of("year").to_date_string()
    end = today.end_of("year").to_date_string()
    return start, end


def get_dates_lastyear():
    lastyear = pendulum.today().subtract(years=1)
    start = lastyear.start_of("year").to_date_string()
    end = lastyear.end_of("year").to_date_string()
    return start, end


def get_dates(
    start,
    end,
    today,
    yesterday,
    thisweek,
    thismonth,
    thisquarter,
    thisyear,
    lastweek,
    lastmonth,
    lastquarter,
    lastyear,
):
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    if today:
        start, end = get_dates_today()
    elif yesterday:
        start, end = get_dates_yesterday()
    elif thisweek:
        start, end = get_dates_thisweek()
    elif thismonth:
        start, end = get_dates_thismonth()
    elif thisquarter:
        start, end = get_dates_thisquarter()
    elif thisyear:
        start, end = get_dates_thisyear()
    elif lastweek:
        start, end = get_dates_lastweek()
    elif lastmonth:
        start, end = get_dates_lastmonth()
    elif lastquarter:
        start, end = get_dates_lastquarter()
    elif lastyear:
        start, end = get_dates_lastyear()
    return start, end


##########################################################################


@click.command()
@click.version_option(version=__version__)
@click.option("--log", default="warning", help="Logging level (info, debug)")
@click.option(
    "--path",
    default=".",
    help="Path where the files containing the time tracking data is stored.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--category",
    default=["All"],
    multiple=True,
    help="Category of time entries to summarise",
    type=click.Choice(["Area", "Focus", "Proj", "Prof", "All"], case_sensitive=False),
)
@click.option(
    "--csv",
    default=False,
    is_flag=True,
    help="Format the output as comma separated values with one row per time entry",
)
@click.option(
    "--tsv",
    default=False,
    is_flag=True,
    help="Format the output as tab separated values",
)
@click.option(
    "--from",
    "from_",
    default=pendulum.today(),
    help="Start of time tracking period (default is today).",
    type=click.DateTime(),
)
@click.option(
    "--to",
    default=pendulum.today(),
    help="End of time tracking period (default is today).",
    type=click.DateTime(),
)
@click.option(
    "--today",
    default=False,
    is_flag=True,
    help="Today's time summary. Overrides --from and --to values.",
)
@click.option(
    "--yesterday",
    default=False,
    is_flag=True,
    help="Yesterday's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisweek",
    default=False,
    is_flag=True,
    help="This week's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thismonth",
    default=False,
    is_flag=True,
    help="This month's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisquarter",
    default=False,
    is_flag=True,
    help="This quarter's time summary. Overrides --from and --to values.",
)
@click.option(
    "--thisyear",
    default=False,
    is_flag=True,
    help="This year's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastweek",
    default=False,
    is_flag=True,
    help="Last week's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastmonth",
    default=False,
    is_flag=True,
    help="Last month's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastquarter",
    default=False,
    is_flag=True,
    help="Last quarter's time summary. Overrides --from and --to values.",
)
@click.option(
    "--lastyear",
    default=False,
    is_flag=True,
    help="Last year's time summary. Overrides --from and --to values.",
)
@click.option(
    "--onsite",
    default=False,
    is_flag=True,
    help="Include onsite information in the summary.",
)
@click.option(
    "--brief", default=False, is_flag=True, help="Brief summary of time entries."
)
def mytime(
    log,
    path,
    category,
    csv,
    tsv,
    from_,
    to,
    today,
    yesterday,
    thisweek,
    thismonth,
    thisquarter,
    thisyear,
    lastweek,
    lastmonth,
    lastquarter,
    lastyear,
    onsite,
    brief,
):
    """Summarize time tracking data.

    Multiple options are provided for specifying the time period. Only the time
    tracking data within the specified time period will be analysed. If no time
    period is specified, today's time tracking info will be analyzed.

    Time tracking information is extracted from 'Daily Note' files which follow
    the convention that there is a separate file for each day and the file name
    follows the pattern: 'YYYY-MM-DD.md', e.g. 2023-10-31.md.
    """
    # Logging setup
    numeric_level = getattr(logging, log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log}")
    logging.basicConfig(format="%(message)s", level=numeric_level)

    # Tune pandas settings
    pd.set_option("display.precision", 2)

    start, end = get_dates(
        from_,
        to,
        today,
        yesterday,
        thisweek,
        thismonth,
        thisquarter,
        thisyear,
        lastweek,
        lastmonth,
        lastquarter,
        lastyear,
    )
    logging.info(f"{start} -> {end}")

    if csv:
        dumpTimeEntries(path, category, start, end)
    else:
        reportTimeSpent(path, category, start, end, tsv, onsite, brief)


##########################################################################

if __name__ == "__main__":
    mytime()
