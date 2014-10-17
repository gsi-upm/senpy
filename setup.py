from distutils.core import setup
setup(
  name = 'senpy',
  packages = ['senpy'], # this must be the same as the name above
  version = '0.2',
  description = '''
    A sentiment analysis server implementation. Designed to be \
extendable, so new algorithms and sources can be used.
    ''',
  author = 'J. Fernando Sanchez',
  author_email = 'balkian@gmail.com',
  url = 'https://github.com/balkian/senpy', # use the URL to the github repo
  download_url = 'https://github.com/balkian/senpy/archive/0.2.tar.gz', # I'll explain this in a second
  keywords = ['eurosentiment', 'sentiment', 'emotions', 'nif'], # arbitrary keywords
  classifiers = [],
)
