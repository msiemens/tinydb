# coding=utf-8
from setuptools import setup, find_packages

setup(
    name = "tinydb",
    version = "0.0.1",
    packages = find_packages(),

    # development metadata
    zip_safe = True,

    # metadata for upload to PyPI
    author = "Markus Siemens",
    author_email = "markus@m-siemens.de",
    description = "TinyDB is a tiny, document oriented database optimized for your happiness :)",
    license = "MIT",
    keywords = "database",
    url = "https://github.com/msiemens/TinyDB",
    classifiers  = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Utilities"
    ],

    long_description = open('README.rst', 'r').read()
    # could also include download_url etc.
)
