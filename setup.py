from setuptools import setup
setup(
    name='mytime',
    version='0.1.0',
    py_modules=['mytime'],
    install_requires=[
        'Click',
        'python-dateutil',
        'tabulate',
    ],
    entry_points={
        'console_scripts': [
            'mytime = mytime:mytime',
        ],
    }
)
