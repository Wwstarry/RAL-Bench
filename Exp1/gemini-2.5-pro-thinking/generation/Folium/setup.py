from setuptools import setup, find_packages

setup(
    name="folium",
    version="0.1.0",
    packages=find_packages(),
    description="A pure-Python library for generating interactive Leaflet.js maps.",
    author="AI Code Generator",
    author_email="ai@example.com",
    package_data={
        'folium': ['templates/*.html'],
    },
    include_package_data=True,
)