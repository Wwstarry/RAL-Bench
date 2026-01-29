"""
Setup script for lifelines package.
"""

from setuptools import setup, find_packages

setup(
    name="lifelines",
    version="0.1.0",
    description="Pure Python survival analysis library",
    author="",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.0.0",
    ],
    python_requires=">=3.7",
)