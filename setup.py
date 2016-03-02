import pip
from setuptools import setup
from pip.req import parse_requirements
# parse_requirements() returns generator of pip.req.InstallRequirement objects

try:
    install_reqs = parse_requirements("requirements.txt", session=pip.download.PipSession())
    test_reqs = parse_requirements("test-requirements.txt", session=pip.download.PipSession())
except AttributeError:
    install_reqs = parse_requirements("requirements.txt")
    test_reqs = parse_requirements("test-requirements.txt")

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
install_reqs = [str(ir.req) for ir in install_reqs]
test_reqs = [str(ir.req) for ir in test_reqs]

exec(open('senpy/__init__.py').read())

setup(
    name='senpy',
    packages=['senpy'],  # this must be the same as the name above
    version=__version__,
    description='''
    A sentiment analysis server implementation. Designed to be \
extendable, so new algorithms and sources can be used.
    ''',
    author='J. Fernando Sanchez',
    author_email='balkian@gmail.com',
    url='https://github.com/gsi-upm/senpy',  # use the URL to the github repo
    download_url='https://github.com/gsi-upm/senpy/archive/{}.tar.gz' .format(__version__),
    keywords=['eurosentiment', 'sentiment', 'emotions', 'nif'],
    classifiers=[],
    install_requires=install_reqs,
    tests_require=test_reqs,
    setup_requires=['pytest-runner',],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'senpy = senpy.__main__:main',
            'senpy-cli = senpy.cli:main'
            ]
        }
)
