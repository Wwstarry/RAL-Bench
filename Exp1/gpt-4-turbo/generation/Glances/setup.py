from setuptools import setup, find_packages

setup(
    name="glances",
    version="0.1.0",
    description="Cross-platform system monitoring tool (Glances CLI-compatible)",
    author="Generated",
    packages=find_packages(),
    install_requires=[
        "psutil",
    ],
    entry_points={
        "console_scripts": [
            "glances=glances.cli:run_cli",
        ],
    },
    python_requires=">=3.6",
)