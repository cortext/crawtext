from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import crawtext

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md', 'CHANGES.md')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import unitest
        errcode = unitest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='crawtext',
    version=crawtext.__version__,
    url='http://github.com/cortext/crawtext/',
    license='MIT',
    author='Constance de Quatrebabres',
    tests_require=['unitest'],
    install_requires=['Jinja2>=2.7.2',
                    'MarkupSafe>=0.19',
                    'Pillow>=2.4.0',
                    'PyYAML>=3.11',
                    'Whoosh>=2.6.0',
                    'beautifulsoup4>=4.3.2'
                    'cssselect>=0.9.1',
                    'docstring>=0.1.2.4',
                    'jieba>=0.32',
                    'pymongo>=3.0.3',
                    'six>=1.4.1',
                    'tld>=0.6.3',
                    'w3lib>=1.10.0'
                    'wsgiref>=0.1.2',
                    'requests>=2.5.3',
                    'readability-lxml>=0.6.1'
                    'langdetect>=1.0.5'
                    'adblockparser>=0.4'
                    'premailer>=2.9.3'
                    ],
    cmdclass={'test': PyTest},
    author_email='4barbes@jgmail.com',
    description='Python Web Crawler query centric',
    long_description=long_description,
    packages=['crawtext'],
    include_package_data=True,
    platforms='any',
    test_suite='sandman.test.test_sandman',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)
