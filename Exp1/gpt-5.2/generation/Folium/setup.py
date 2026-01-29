from setuptools import setup, find_packages

setup(
    name="folium",
    version="0.0.0",
    description="Minimal pure-Python Leaflet HTML generator compatible with core Folium APIs (subset).",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
)