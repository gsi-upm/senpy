PYVERSIONS ?= 3.5
PYMAIN ?= $(firstword $(PYVERSIONS))
TARNAME ?= $(NAME)-$(VERSION).tar.gz 
VERSIONFILE ?= $(NAME)/VERSION

DEVPORT ?= 6000


.FORCE:

version: .FORCE
	@echo $(VERSION) > $(VERSIONFILE)
	@echo $(VERSION)

yapf: ## Format python code
	yapf -i -r $(NAME)
	yapf -i -r tests

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS)) ## Generate dockerfiles for each python version
	@unlink Dockerfile >/dev/null
	ln -s Dockerfile-$(PYMAIN) Dockerfile

Dockerfile-%: Dockerfile.template  ## Generate a specific dockerfile (e.g. Dockerfile-2.7)
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

quick_build: $(addprefix build-, $(PYMAIN))

build: $(addprefix build-, $(PYVERSIONS)) ## Build all images / python versions

build-%: version Dockerfile-%  ## Build a specific version (e.g. build-2.7)
	docker build -t '$(IMAGEWTAG)-python$*' -f Dockerfile-$* .;

dev-%: ## Launch a specific development environment using docker (e.g. dev-2.7)
	@docker start $(NAME)-dev$* || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -p $(DEVPORT):5000 -v $$PWD:/usr/src/app --entrypoint=/bin/bash -ti --name $(NAME)-dev$* '$(IMAGEWTAG)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev$* bash

dev: dev-$(PYMAIN) ## Launch a development environment using docker, using the default python version

quick_test: test-$(PYMAIN)

test-%: build-% ## Run setup.py from in an isolated container, built from the base image. (e.g. test-2.7)
# This speeds tests up because the image has most (if not all) of the dependencies already.
	docker rm $(NAME)-test-$* || true
	docker create -ti --name $(NAME)-test-$* --entrypoint="" -w /usr/src/app/ $(IMAGEWTAG)-python$* python setup.py test
	docker cp . $(NAME)-test-$*:/usr/src/app
	docker start -a $(NAME)-test-$*

test: $(addprefix test-,$(PYVERSIONS)) ## Run the tests with the main python version

run-%: build-%
	docker run --rm -p $(DEVPORT):5000 -ti '$(IMAGEWTAG)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

# Pypy - Upload a package

dist/$(TARNAME): version
	python setup.py sdist;

sdist: dist/$(TARNAME) ## Generate the distribution file (wheel)

pip_test-%: sdist ## Test the distribution file using pip install and a specific python version (e.g. pip_test-2.7)
	docker run --rm -v $$PWD/dist:/dist/ python:$* pip install /dist/$(TARNAME);

pip_test: $(addprefix pip_test-,$(PYVERSIONS)) ## Test pip installation with the main python version

pip_upload: pip_test  ## Upload package to pip
	python setup.py sdist upload ;

# Pushing to docker

push-latest: $(addprefix push-latest-,$(PYVERSIONS)) ## Push the "latest" tag to dockerhub
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGENAME)'
	docker push '$(IMAGENAME):latest'
	docker push '$(IMAGEWTAG)'

push-latest-%: build-%  ## Push the latest image for a specific python version
	docker tag $(IMAGENAME):$(VERSION)-python$* $(IMAGENAME):python$*
	docker push $(IMAGENAME):$(VERSION)-python$*
	docker push $(IMAGENAME):python$*

push-%: build-%  ## Push the image of the current version (tagged). e.g. push-2.7
	docker push $(IMAGENAME):$(VERSION)-python$*

push:: $(addprefix push-,$(PYVERSIONS)) ## Push an image with the current version for every python version
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker push  $(IMAGENAME):$(VERSION)

clean:: ## Clean older docker images and containers related to this project and dev environments
	@docker stop $(addprefix $(NAME)-dev,$(PYVERSIONS)) 2>/dev/null || true
	@docker rm $(addprefix $(NAME)-dev,$(PYVERSIONS)) 2>/dev/null || true
	@docker ps -a | grep $(IMAGENAME) | awk '{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1;}}' | xargs docker rm -v 2>/dev/null|| true
	@docker images | grep $(IMAGENAME) | awk '{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true

.PHONY:: yapf dockerfiles Dockerfile-% quick_build build build-% dev-% quick-dev test quick_test push-latest push-latest-% push-% push version .FORCE
