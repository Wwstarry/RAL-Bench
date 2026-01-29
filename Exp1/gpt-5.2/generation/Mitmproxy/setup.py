from setuptools import setup, find_packages

setup(
    name="mitmproxy",
    version="0.0.0",
    description="Minimal safe-to-evaluate subset of mitmproxy for tests",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "mitmdump=mitmproxy.tools.main.mitmdump:main",
        ]
    },
)