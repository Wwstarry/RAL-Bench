from setuptools import setup, find_packages

setup(
    name="fail2ban-min",
    version="0.1.0",
    description="Minimal safe-to-evaluate subset of Fail2Ban for offline regex matching.",
    packages=find_packages(),
    package_data={"fail2ban": ["../config/jail.conf"]},
    include_package_data=True,
    python_requires=">=3.8",
)