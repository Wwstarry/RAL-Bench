from setuptools import setup, find_packages

setup(
    name="lifelines",
    version="0.0.0",
    description="Minimal pure Python survival analysis library (API-compatible subset).",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
)