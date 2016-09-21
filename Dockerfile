from gsiupm/senpy:0.6.1-python2.7

RUN mkdir -p /senpy-plugins
RUN pip install nltk
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader maxent_treebank_pos_tagger
RUN python -m nltk.downloader wordnet

RUN pip install pytest
RUN pip install mock
ADD . /senpy-plugins
RUN senpy -f /senpy-plugins --only-install

WORKDIR /senpy-plugins/
