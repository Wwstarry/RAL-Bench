"""
Setup script for astral package.
"""

from setuptools import setup, find_packages

setup(
    name="astral",
    version="3.0",
    description="Pure Python sun and moon time calculation library",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pytz",
    ],
)