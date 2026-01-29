from setuptools import setup, find_packages

setup(
    name="glances",
    version="3.4.0.3",
    packages=find_packages(),
    install_requires=["psutil"],
)