# Copyright 2016 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

VERSION = '0.4.0'

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.rst').read()
except Exception:
    pass


CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    'Topic :: Database',
    'Topic :: Software Development :: Libraries :: Python Modules',
]


requires = ['pymongo>=3.4']
if sys.version_info[:2] == (2, 7):
    requires.append('ipaddress')

setup(
    name='pymodm',
    version=VERSION,
    author='Luke Lovett',
    author_email='luke.lovett@{nospam}mongodb.com',
    license='Apache License, Version 2.0',
    include_package_data=True,
    description='PyMODM is a generic ODM on top of PyMongo.',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(exclude=['test', 'test.*']),
    platforms=['any'],
    classifiers=CLASSIFIERS,
    test_suite='test',
    install_requires=requires,
    extras_require={'images': 'Pillow'}
)
