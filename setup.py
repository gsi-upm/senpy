from setuptools import setup

with open('senpy/VERSION') as f:
    __version__ = f.read().strip()
    assert __version__


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    with open(filename, 'r') as f:
        lineiter = list(line.strip() for line in f)
    return [line for line in lineiter if line and not line.startswith("#")]


install_reqs = parse_requirements("requirements.txt")
test_reqs = parse_requirements("test-requirements.txt")
extra_reqs = parse_requirements("extra-requirements.txt")


setup(
    name='senpy',
    python_requires='>3.3',
    packages=['senpy'],  # this must be the same as the name above
    version=__version__,
    description=('A sentiment analysis server implementation. '
                 'Designed to be extensible, so new algorithms '
                 'and sources can be used.'),
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
        'evaluation': extra_reqs
    },
    include_package_data=True,
    entry_points={
        'console_scripts':
        ['senpy = senpy.__main__:main', 'senpy-cli = senpy.cli:main']
    })
