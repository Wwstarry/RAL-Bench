from setuptools import setup, find_packages

setup(
    name='fail2ban',
    version='0.11.0',
    description='Fail2Ban - Intrusion prevention framework',
    author='Fail2Ban Team',
    url='https://www.fail2ban.org',
    packages=find_packages(),
    scripts=[
        'bin/fail2ban-client',
        'bin/fail2ban-server',
        'bin/fail2ban-regex',
    ],
    data_files=[
        ('config', ['config/jail.conf']),
    ],
    python_requires='>=3.6',
)