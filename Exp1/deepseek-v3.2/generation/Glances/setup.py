from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="glances",
    version="3.5.0",
    author="Glances Team",
    author_email="contact@nicolargo.com",
    description="A cross-platform system monitoring tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nicolargo/glances",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
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
    python_requires=">=3.6",
    install_requires=[
        "psutil>=5.7.0",
    ],
    entry_points={
        "console_scripts": [
            "glances=glances.cli:main",
        ],
    },
)