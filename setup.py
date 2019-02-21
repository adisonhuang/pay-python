#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/17

from __future__ import print_function

import codecs
import os
import sys

try:
    from setuptools import setup
except:
    from distutils.core import setup

try:
    # python setup.py test
    import multiprocessing  # NOQA
except ImportError:
    pass

from setuptools import find_packages

if sys.version_info < (2, 7):
    sys.exit('Python 2.7 or greater is required.')

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst', 'rb') as fp:
    readme = fp.read()

with open('requirements.txt') as f:
    requirements = [l for l in f.read().splitlines() if l]

VERSION = "1.0.3"

LICENSE = "MIT"

setup(
    name='all_pay',
    version=VERSION,
    description='Python SDK for multi pay ,such as AliPay、WeChatpay',
    long_description=readme,
    author='adison',
    author_email='adison5321@gmail.com',
    maintainer='adison',
    maintainer_email='adison5321@gmail.com',
    license=LICENSE,
    packages=find_packages(),
    keywords='WeChatpay, AliPay,Pay',
    url='https://github.com/adisonhuang/pay-python',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
