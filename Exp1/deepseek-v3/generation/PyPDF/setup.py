from setuptools import setup, find_packages

setup(
    name="pypdf",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.6",
    author="PDF Library",
    description="A pure Python PDF manipulation library",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)