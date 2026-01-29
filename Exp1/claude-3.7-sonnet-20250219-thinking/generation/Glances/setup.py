from setuptools import setup, find_packages

setup(
    name="glances",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'glances=glances.cli:main',
        ],
    },
    install_requires=[],
    python_requires='>=3.6',
)