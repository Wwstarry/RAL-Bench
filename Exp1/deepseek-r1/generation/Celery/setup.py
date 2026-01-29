from setuptools import setup, find_packages

setup(
    name="celery-minimal",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.6",
    author="Celery Minimal",
    description="Minimal Celery-compatible task queue",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)