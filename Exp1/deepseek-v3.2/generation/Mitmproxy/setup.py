from setuptools import setup, find_packages

setup(
    name="mitmproxy",
    version="10.0.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "mitmdump = mitmproxy.tools.main:mitmdump",
        ],
    },
    python_requires=">=3.8",
)