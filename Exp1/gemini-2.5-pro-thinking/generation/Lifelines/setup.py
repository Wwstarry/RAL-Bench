from setuptools import setup, find_packages

setup(
    name="lifelines",
    version="0.25.0",  # Mimic a realistic version
    packages=find_packages(),
    author="Generated AI",
    description="A pure Python implementation of survival analysis",
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "scipy>=1.4.0",
    ],
    python_requires=">=3.7",
)