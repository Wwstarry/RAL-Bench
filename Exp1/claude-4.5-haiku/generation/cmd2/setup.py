"""
Setup configuration for cmd2 package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cmd2",
    version="1.0.0",
    author="Anthropic",
    description="A pure Python interactive command-line application framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anthropic/cmd2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)