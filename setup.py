#!/usr/bin/env python

import os
from setuptools import setup

def _read_file(fn):
    with open(fn) as f:
        return f.read()

VERSION = '0.2.1'
LONG_DESCRIPTION = _read_file(os.path.join(
    os.path.dirname(__file__),
    'README.rst'))

setup(
    name="dbghelper",
    version=VERSION,
    author = "David Fraser",
    author_email = 'davidf@sjsoft.com',
    url = 'https://github.com/davidfraser/dbghelper',
    description = 'Simple helper for inline winpdb/pdb debugging',
    long_description = LONG_DESCRIPTION,
    license='BSD',
    py_modules=['dbg'],
    install_requires = ['winpdb'],
)

