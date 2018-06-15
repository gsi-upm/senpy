PYVERSION=2.7
NAME=senpycommunity
REPO=gsiupm
PLUGINS= $(filter %/, $(wildcard */))
IMAGENAME=gsiupm/senpy-plugins-community
DOCKER_FLAGS=-p 5000:5000

ifdef SENPY_FOLDER
	DOCKER_FLAGS+= -v $(realpath $(SENPY_FOLDER)):/usr/src/app/
	endif


all: build run

test-%:
	docker run $(DOCKER_FLAGS) -v $$PWD/$*:/senpy-plugins/ -v $$PWD/data:/data/ --rm $(IMAGEWTAG) --only-test $(TEST_FLAGS)

test: test-.

clean-docker:
	@docker ps -a | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1;}}' | xargs docker rm 2>/dev/null|| true
	@docker images | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true

.PHONY:: test test-% build-% build test test_pip run clean

include .makefiles/base.mk
include .makefiles/k8s.mk

