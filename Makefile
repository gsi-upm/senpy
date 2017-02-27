PYVERSIONS=3.5 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell git describe --tags --dirty 2>/dev/null)
TARNAME=$(NAME)-$(VERSION).tar.gz 
IMAGENAME=$(REPO)/$(NAME)
IMAGEWTAG=$(IMAGENAME):$(VERSION)
action="test-${PYMAIN}"

all: build run

.FORCE:

version: .FORCE
	@echo $(VERSION) > $(NAME)/VERSION
	@echo $(VERSION)

yapf:
	yapf -i -r senpy
	yapf -i -r tests

init:
	pip install --user pre-commit
	pre-commit install

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS))
	@unlink Dockerfile >/dev/null
	ln -s Dockerfile-$(PYMAIN) Dockerfile

Dockerfile-%: Dockerfile.template
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

quick_build: $(addprefix build-, $(PYMAIN))

build: $(addprefix build-, $(PYVERSIONS))

build-%: version Dockerfile-%
	docker build -t '$(IMAGEWTAG)-python$*' -f Dockerfile-$* .;

quick_test: $(addprefix test-,$(PYMAIN))

dev-%:
	@docker start $(NAME)-dev || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -v $$PWD:/usr/src/app --entrypoint=/bin/bash -p 5000:5000 -ti --name $(NAME)-dev '$(IMAGEWTAG)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev bash

dev: dev-$(PYMAIN)

test-all: $(addprefix test-,$(PYVERSIONS))

test-%: build-%
	docker run --rm --entrypoint /usr/local/bin/python -w /usr/src/app $(IMAGEWTAG)-python$*  setup.py test

test: test-$(PYMAIN)

dist/$(TARNAME):
	docker run --rm -ti -v $$PWD:/usr/src/app/ -w /usr/src/app/ python:$(PYMAIN) python setup.py sdist;

sdist: dist/$(TARNAME)

pip_test-%: sdist
	docker run --rm -v $$PWD/dist:/dist/ -ti python:$* pip install /dist/$(TARNAME);

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

clean:
	@docker ps -a | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1;}}' | xargs docker rm -v 2>/dev/null|| true
	@docker images | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true
	@docker rmi $(NAME)-dev 2>/dev/null || true


git_commit:
	git commit -a

git_tag:
	git tag ${VERSION}

git_push:
	git push --tags origin master

pip_upload:
	python setup.py sdist upload ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

run-%: build-%
	docker run --rm -p 5000:5000 -ti '$(IMAGEWTAG)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

push-latest: build-$(PYMAIN)
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGENAME)'
	docker push '$(IMAGENAME)'
	docker push '$(IMAGEWTAG)'

push-%: build-%
	docker push $(IMAGENAME):$(VERSION)-python$*

ci:
	gitlab-runner exec docker --docker-volumes /var/run/docker.sock:/var/run/docker.sock --env CI_PROJECT_NAME=$(NAME) ${action}

.PHONY: test test-% test-all build-% build test pip_test run yapf push-main push-% dev ci version .FORCE
