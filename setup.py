# coding=utf-8
from setuptools import setup, find_packages

setup(
    name = "TinyDB",
    version = "0.0.1",
    packages = find_packages(),

    # development metadata
    zip_safe = True,

    # metadata for upload to PyPI
    author = "Markus Siemens",
    author_email = "markus@m-siemens.de",
    description = "A tiny, intuitive database written in pure Python",
    license = "MIT",
    keywords = "database",
    url = "https://github.com/msiemens/TinyDB",
    classifiers  = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Version Control",
        "Topic :: Utilities"
    ],

    long_description = open('README.rst', 'r').read()
    # could also include download_url etc.
)
