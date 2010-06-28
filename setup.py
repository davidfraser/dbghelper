#!/usr/bin/env python

from setuptools import setup

VERSION = '0.1'

setup(  name="dbghelper", version=VERSION,
        author = "David Fraser",
        author_email = 'davidf@sjsoft.com',
	url = 'http://bitbucket.org/davidfraser/python-dbghelper',
        description = 'Simple helper for inline winpdb/pdb debugging',
        license='BSD',
	py_modules=['dbg'],
        install_requires = ['winpdb'],
)

