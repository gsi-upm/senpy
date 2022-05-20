'''
Copyright 2014 GSI DIT UPM

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from setuptools import setup
from os import path
import io

try:
    with io.open('senpy/VERSION') as f:
        __version__ = f.read().strip()
        assert __version__
except IOError:  # pragma: no cover
    print('Installing a development version of senpy. Proceed with caution!')
    __version__ = 'devel'


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    with io.open(filename, 'r') as f:
        lineiter = list(line.strip() for line in f)
    return [line for line in lineiter if line and not line.startswith("#")]


this_directory = path.abspath(path.dirname(__file__))
with io.open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


install_reqs = parse_requirements("requirements.txt")
test_reqs = parse_requirements("test-requirements.txt")
extra_reqs = parse_requirements("extra-requirements.txt")


setup(
    name='senpy',
    python_requires='>3.6',
    packages=['senpy'],  # this must be the same as the name above
    version=__version__,
    description=('A sentiment analysis server implementation. '
                 'Designed to be extensible, so new algorithms '
                 'and sources can be used.'),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='J. Fernando Sanchez',
    author_email='balkian@gmail.com',
    url='https://github.com/gsi-upm/senpy',  # use the URL to the github repo
    download_url='https://github.com/gsi-upm/senpy/archive/{}.tar.gz'.format(
        __version__),
    keywords=['eurosentiment', 'sentiment', 'emotions', 'nif'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    install_requires=install_reqs,
    tests_require=test_reqs,
    setup_requires=['pytest-runner', ],
    extras_require={
        'evaluation': extra_reqs,
        'extras': extra_reqs
    },
    include_package_data=True,
    entry_points={
        'console_scripts':
        ['senpy = senpy.__main__:main', 'senpy-cli = senpy.cli:main']
    })
