"""
Setup configuration for pypdf.
"""

from setuptools import setup, find_packages

setup(
    name="pypdf",
    version="0.1.0",
    description="A pure Python PDF manipulation library",
    author="Generated",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)