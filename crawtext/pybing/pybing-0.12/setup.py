# This file is part of PyBing (http://pybing.googlecode.com).
# 
# Copyright (C) 2009 JJ Geewax http://geewax.org/
# All rights reserved.
# 
# This software is licensed as described in the file COPYING.txt,
# which you should have received as part of this distribution.

from setuptools import setup, find_packages
import sys, os

version = '0.12'

requirements = ['httplib2']

# For Python 2.5 and below, we need simplejson
if sys.version_info < (2, 6):
    requirements += ['simplejson']

setup(
    name='pybing',
    version=version,
    description="PyBing is a Python wrapper for the Bing Search API",
    long_description="""\
PyBing is a Python wrapper for the Bing Search API""",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='bing api',
    author='JJ Geewax',
    author_email='jj@geewax.org',
    url='http://pybing.googlecode.com/',
    license='GPL v2',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=True,
    install_requires=requirements,
)
