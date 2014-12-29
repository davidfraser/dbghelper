#!/usr/bin/env python

from setuptools import setup

VERSION = '0.2'

setup(
    name="dbghelper",
    version=VERSION,
    author = "David Fraser",
    author_email = 'davidf@sjsoft.com',
    url = 'https://github.com/davidfraser/dbghelper',
    description = 'Simple helper for inline winpdb/pdb debugging',
    license='BSD',
    py_modules=['dbg'],
    install_requires = ['winpdb'],
)

