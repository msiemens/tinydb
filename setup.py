# coding=utf-8
from setuptools import setup, find_packages

setup(
    name="tinydb",
    version="1.3.0",
    packages=find_packages(),

    # development metadata
    zip_safe=True,

    # metadata for upload to PyPI
    author="Markus Siemens",
    author_email="markus@m-siemens.de",
    description="TinyDB is a tiny, document oriented database optimized for "
                "your happiness :)",
    license="MIT",
    keywords="database nosql",
    url="https://github.com/msiemens/tinydb",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Operating System :: OS Independent"
    ],

    long_description=open('README.rst', 'r').read(),
)
