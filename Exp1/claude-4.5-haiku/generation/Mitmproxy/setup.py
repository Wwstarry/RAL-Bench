"""
Setup configuration for mitmproxy.
"""

from setuptools import setup, find_packages

setup(
    name="mitmproxy",
    version="10.0.0",
    description="An interactive TLS-capable intercepting proxy",
    author="Anthropic",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "mitmdump=mitmproxy.tools.main:mitmdump",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)