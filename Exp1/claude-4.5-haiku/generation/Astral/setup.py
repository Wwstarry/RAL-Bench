"""
Setup configuration for astral package.
"""

from setuptools import setup, find_packages

setup(
    name='astral',
    version='1.0.0',
    description='A pure Python sun and moon time calculation library',
    author='Generated',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'pytz',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)