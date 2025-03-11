#!/usr/bin/env python

from setuptools import setup

requires = [
    'chardet==3.0.4',
    'click==6.7',
    'flake8==3.5.0',
    'Flask==0.12.3',
    'gnureadline==6.3.8',
    'idna==2.6',
    'IPy==0.83',
    'itsdangerous==0.24',
    'MarkupSafe==1.0',
    'mock==2.0.0',
    'pytest==3.3.2',
    'pytest-runner==3.0',
    'requests==2.18.4',
    'urllib3==1.22',
    'WebOb==1.7.4',
    'Werkzeug==0.15.3',
    'zappa==0.45.1'
]

test_requirements = [
    'mock',
    'pytest'
]

setup(
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requires,
    zip_safe=True,
    tests_require=test_requirements,
    setup_requires=['pytest-runner'],
)
