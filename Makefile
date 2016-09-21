PYVERSIONS=3.4 2.7
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

upload-%:
	docker push '$(REPO)/$(NAME):$(VERSION)-python$(firstword $(PYVERSIONS))'

upload: test $(addprefix upload-,$(PYVERSIONS))
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(firstword $(PYVERSIONS))' '$(REPO)/$(NAME):$(VERSION)'
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(firstword $(PYVERSIONS))' '$(REPO)/$(NAME)'
	docker push '$(REPO)/$(NAME):$(VERSION)'
	docker push '$(REPO)/$(NAME)'

test_pip: $(addprefix test_pip-,$(PYVERSIONS))

.PHONY: test test-% build-% build test test_pip
