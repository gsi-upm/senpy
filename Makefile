PYVERSIONS=2.7 3.4
NAME=senpy
REPO=gsiupm
VERSION=$(shell cat $(NAME)/VERSION)


all: build run

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS))

Dockerfile-%: Dockerfile.template
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

build: $(addprefix build-, $(PYVERSIONS))

build-%: Dockerfile-%
	docker build -t '$(REPO)/$(NAME):$(VERSION)-python$*' -f Dockerfile-$* .;

test: $(addprefix test-,$(PYVERSIONS))

test-%: build-%
	docker run --rm -w /usr/src/app/ --entrypoint=/usr/local/bin/python -ti '$(REPO)/$(NAME):$(VERSION)-python$*' setup.py test ;

test_pip-%:
	docker run --rm -ti python:$* pip -q install senpy ;
    
test_pip: $(addprefix test_pip-,$(PYVERSIONS))

.PHONY: test test-% build-% build test test_pip
