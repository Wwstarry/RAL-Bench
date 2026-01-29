"""Setup script for Glances."""
from setuptools import setup, find_packages

setup(
    name="glances",
    version="3.4.0.1",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.0.0",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "glances=glances.cli:main",
        ],
    },
    author="Glances Team",
    description="A cross-platform system monitoring tool",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: LGPL License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)