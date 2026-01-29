from setuptools import setup, find_packages

setup(
    name="lifelines-compat",
    version="0.1.0",
    description="Pure Python survival analysis library compatible with lifelines API",
    author="Generated",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.0.0",
    ],
    python_requires=">=3.7",
)