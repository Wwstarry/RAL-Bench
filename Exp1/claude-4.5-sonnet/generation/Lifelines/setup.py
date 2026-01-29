from setuptools import setup, find_packages

setup(
    name='lifelines',
    version='0.1.0',
    description='Survival analysis in Python',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.14.0',
        'pandas>=0.23.0',
        'scipy>=1.0.0',
    ],
    python_requires='>=3.6',
)