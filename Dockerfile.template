from python:{{PYVERSION}}

MAINTAINER J. Fernando Sánchez <jf.sanchez@upm.es>

RUN apt-get update && apt-get install -y \
libblas-dev liblapack-dev liblapacke-dev gfortran \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /cache/ /senpy-plugins /data/

VOLUME /data/

ENV PIP_CACHE_DIR=/cache/ SENPY_DATA=/data

ONBUILD COPY . /senpy-plugins/
ONBUILD RUN python -m senpy --only-install -f /senpy-plugins
ONBUILD WORKDIR /senpy-plugins/


WORKDIR /usr/src/app
COPY test-requirements.txt requirements.txt extra-requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r test-requirements.txt -r requirements.txt -r extra-requirements.txt
COPY . /usr/src/app/
RUN pip install --no-cache-dir --no-index --no-deps --editable .

ENTRYPOINT ["python", "-m", "senpy", "-f", "/senpy-plugins/", "--host", "0.0.0.0"]
