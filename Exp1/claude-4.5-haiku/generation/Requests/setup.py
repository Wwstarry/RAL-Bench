from setuptools import setup, find_packages

setup(
    name="requests-test",
    version="0.1.0",
    description="Test suite for requests library core APIs",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
        ],
    },
    python_requires=">=3.6",
)