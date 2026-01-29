"""
Setup script for stegano package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stegano",
    version="0.11.3",
    author="Stegano Contributors",
    description="A pure Python steganography library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stegano/stegano",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "Pillow>=8.0.0",
        "piexif>=1.1.3",
    ],
    entry_points={
        "console_scripts": [
            "stegano=stegano.console.main:main",
        ],
    },
)