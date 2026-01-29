from setuptools import setup, find_packages

setup(
    name='mailpile-benchmark',
    version='0.1.0',
    description='Mailpile core library benchmark suite',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'pytest>=6.0',
    ],
)