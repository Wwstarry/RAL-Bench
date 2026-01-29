# setup.py
from setuptools import setup, find_packages

setup(
    name="fail2ban-subset",
    version="0.1.0",
    packages=find_packages(),
    scripts=[
        'bin/fail2ban-client',
        'bin/fail2ban-server',
        'bin/fail2ban-regex'
    ],
    author="Benchmark Generator",
    author_email="generator@example.com",
    description="A minimal, safe-to-evaluate subset of Fail2Ban.",
    long_description="""
    This package provides a minimal, non-daemon, safe-to-evaluate subset of
    the Fail2Ban intrusion prevention framework. It focuses on validating
    core API surface, configuration artifacts, and regex-based log matching
    behavior in a safe offline manner.
    """,
    url="https://github.com/example/fail2ban-subset",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)