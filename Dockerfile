from python:2.7

RUN apt-get update
RUN apt-get -y install git
RUN mkdir -p /senpy-plugins

RUN apt-get -y install python-numpy
RUN apt-get -y install python-scipy
RUN apt-get -y install python-sklearn
RUN apt-get -y install python-gevent
RUN apt-get -y install libopenblas-dev
RUN apt-get -y install gfortran
RUN apt-get -y install libxml2-dev libxslt1-dev python-dev

#RUN pip install --upgrade pip

ADD id_rsa /root/.ssh/id_rsa
RUN chmod 700 /root/.ssh/id_rsa
RUN echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

RUN git clone https://github.com/gsi-upm/senpy /usr/src/app/
RUN git clone git@github.com:gsi-upm/senpy-plugins-enterprise /senpy-plugins/enterprise
RUN git clone https://github.com/gsi-upm/senpy-plugins-community /senpy-plugins/community

RUN pip install /usr/src/app
RUN pip install --no-use-wheel -r /senpy-plugins/enterprise/requirements.txt
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader maxent_treebank_pos_tagger
RUN python -m nltk.downloader wordnet

WORKDIR /senpy-plugins
ENTRYPOINT ["python", "-m", "senpy", "-f", ".", "--host", "0.0.0.0"]
