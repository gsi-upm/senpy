PYVERSIONS=3.4 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell cat $(NAME)/VERSION)


all: build run

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS))

Dockerfile-%: Dockerfile.template
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

build: $(addprefix build-, $(PYMAIN))

buildall: $(addprefix build-, $(PYVERSIONS))

build-%: Dockerfile-%
	docker build -t '$(REPO)/$(NAME):$(VERSION)-python$*' -f Dockerfile-$* .;

test: $(addprefix test-,$(PYMAIN))

testall: $(addprefix test-,$(PYVERSIONS))

test-%: build-%
	docker run --rm -w /usr/src/app/ --entrypoint=/usr/local/bin/python -ti '$(REPO)/$(NAME):$(VERSION)-python$*' setup.py test --addopts "-vvv -s --pdb" ;

pip_test-%:
	docker run --rm -ti python:$* pip install senpy ;

upload-%: test-%
	docker push '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)'

upload: testall $(addprefix upload-,$(PYVERSIONS))
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)' '$(REPO)/$(NAME):$(VERSION)'
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(PYVERSIONS)' '$(REPO)/$(NAME)'
	docker push '$(REPO)/$(NAME):$(VERSION)' docker push '$(REPO)/$(NAME)'
	python setup.py sdist upload

pip_upload:
	python setup.py sdist upload ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

run: build
	docker run --rm -p 5000:5000 -ti '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)'

.PHONY: test test-% build-% build test test_pip run
