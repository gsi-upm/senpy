PYVERSIONS=3.5 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell git describe --tags --dirty 2>/dev/null)
TARNAME=$(NAME)-$(VERSION).tar.gz 
IMAGENAME=$(REPO)/$(NAME):$(VERSION)
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
	docker build -t '$(IMAGENAME)-python$*' -f Dockerfile-$* .;

quick_test: $(addprefix test-,$(PYMAIN))

dev-%:
	@docker start $(NAME)-dev || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -v $$PWD:/usr/src/app --entrypoint=/bin/bash -p 5000:5000 -ti --name $(NAME)-dev '$(IMAGENAME)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev bash

dev: dev-$(PYMAIN)

test-all: $(addprefix test-,$(PYVERSIONS))

test-%: build-%
	docker run --rm --entrypoint /usr/local/bin/python -w /usr/src/app $(IMAGENAME)-python$*  setup.py test

test: test-$(PYMAIN)

dist/$(TARNAME):
	docker run --rm -ti -v $$PWD:/usr/src/app/ -w /usr/src/app/ python:$(PYMAIN) python setup.py sdist;

sdist: dist/$(TARNAME)

pip_test-%: sdist
	docker run --rm -v $$PWD/dist:/dist/ -ti python:$* pip install /dist/$(TARNAME);

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

upload-%: test-%
	docker push '$(IMAGENAME)-python$*'

upload: test $(addprefix upload-,$(PYVERSIONS))
	docker tag '$(IMAGENAME)-python$(PYMAIN)' '$(IMAGENAME)'
	docker tag '$(IMAGENAME)-python$(PYMAIN)' '$(REPO)/$(NAME)'
	docker push '$(IMAGENAME)'
	docker push '$(REPO)/$(NAME)'

clean:
	@docker ps -a | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1;}}' | xargs docker rm -v 2>/dev/null|| true
	@docker images | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true
	@docker rmi $(NAME)-dev 2>/dev/null || true


git_commit:
	git commit -a

git_tag:
	git tag ${VERSION}

upload_git:
	git push --tags origin master

pip_upload:
	python setup.py sdist upload ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

run-%: build-%
	docker run --rm -p 5000:5000 -ti '$(IMAGENAME)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

push-latest: build-$(PYMAIN)
	docker tag $(IMAGENAME)-python$(PYMAIN) $(IMAGENAME)
	docker push $(IMAGENAME)

push-%: build-%
	docker push $(IMAGENAME)-python$*

ci:
	gitlab-runner exec docker --docker-volumes /var/run/docker.sock:/var/run/docker.sock --env CI_PROJECT_NAME=$(NAME) ${action}

.PHONY: test test-% test-all build-% build test pip_test run yapf dev ci version .FORCE
