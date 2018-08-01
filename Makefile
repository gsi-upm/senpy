PYVERSION=2.7
NAME=senpycommunity
REPO=gsiupm
PLUGINS= $(filter %/, $(wildcard */))
IMAGENAME=gsiupm/senpy-plugins-community
DOCKER_FLAGS=-e MOCK_REQUESTS=$(MOCK_REQUESTS)
DEV_PORT?=5000

ifdef SENPY_FOLDER
	DOCKER_FLAGS+= -v $(realpath $(SENPY_FOLDER)):/usr/src/app/
	endif

all: build run

test-fast-%:
	docker run $(DOCKER_FLAGS) -v $$PWD/$*:/senpy-plugins/ -v $$PWD/data:/data/ --rm $(IMAGEWTAG) --only-test $(TEST_FLAGS)

test-fast: test-fast-/

test: docker-build test-fast

dev:
	docker run -p $(DEV_PORT):5000 $(DOCKER_FLAGS) -ti $(DOCKER_FLAGS) -v $$PWD/$*:/senpy-plugins/ --entrypoint /bin/bash -v $$PWD/data:/data/ --rm $(IMAGEWTAG)

.PHONY:: test test-fast  dev

include .makefiles/base.mk
include .makefiles/k8s.mk

