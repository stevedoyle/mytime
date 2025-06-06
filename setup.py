from setuptools import setup
from version import __version__

setup(
    name="mytime",
    version=__version__,
    py_modules=["mytime", "myday"],
    install_requires=[
        "Click",
        "python-dateutil",
        "tabulate",
        "pandas",
        "pendulum",
    ],
    entry_points={
        "console_scripts": [
            "mytime = mytime:mytime",
            "myday = myday:main",
        ],
    },
)
