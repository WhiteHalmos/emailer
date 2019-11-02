#!/usr/bin/env python

import setuptools

import emailer

with open('README.md') as f:
  long_description = f.read()

setuptools.setup(
    name=emailer.__name__,
    version=emailer.__version__,
    description=emailer.__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=emailer.__url__,
    author=emailer.__author__,
    author_email=emailer.__author_email__,
    license=emailer.__license__,
    packages=[emailer.__name__],
    python_requires='>=3.7',
    include_package_data=True,
    install_requires=[
        'google-api-python-client',
        'google-auth-oauthlib',
        'mistune',
    ],
    entry_points={
        'console_scripts': [
            'emailer = emailer.__main__:main',
        ],
    },
)
