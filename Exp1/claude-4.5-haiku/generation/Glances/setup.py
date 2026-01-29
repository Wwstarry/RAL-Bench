"""Setup configuration for Glances."""

from setuptools import setup, find_packages
from glances import __version__

setup(
    name="glances",
    version=__version__,
    description="A cross-platform system monitoring tool",
    author="Nicolas Hennion",
    license="LGPL",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "psutil>=5.3.0",
    ],
    entry_points={
        "console_scripts": [
            "glances=glances.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Monitoring",
    ],
)