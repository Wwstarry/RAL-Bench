"""
Setup script for mitmproxy.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mitmproxy",
    version="10.0.0",
    author="Mitmproxy Project",
    author_email="cortesi@gmail.com",
    description="An interactive TLS-capable intercepting HTTP proxy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://mitmproxy.org",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "mitmdump=mitmproxy.tools.main:mitmdump",
            "mitmproxy=mitmproxy.tools.main:mitmproxy_console",
            "mitmweb=mitmproxy.tools.main:mitmweb",
        ],
    },
)