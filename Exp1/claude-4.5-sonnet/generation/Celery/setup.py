"""
Setup script for celery
"""

from setuptools import setup, find_packages

setup(
    name='celery',
    version='5.3.0',
    description='Distributed Task Queue',
    author='Ask Solem',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)