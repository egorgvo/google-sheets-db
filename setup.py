import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="google-sheets-db",
    version='1.0.8',
    description="Google Sheets as a database ORM",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/egorgvo/google-sheets-db",
    author="Egor Gvo",
    author_email="work.egvo@ya.ru",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=["google_sheets_db"],
    install_requires=["oauth2client==3.0.0", "gspread==3.6.0", "pandas>=1.3.1"],
    include_package_data=True,
)
