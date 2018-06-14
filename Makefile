PYVERSION=2.7
NAME=senpycommunity
REPO=gsiupm
VERSION=test
PLUGINS= $(filter %/, $(wildcard */))
DOCKER_FLAGS=

ifdef SENPY_FOLDER
	DOCKER_FLAGS+=-v $(realpath $(SENPY_FOLDER)):/usr/src/app/
	endif


all: build run

build: clean Dockerfile
	docker build -t '$(REPO)/$(NAME):$(VERSION)-python$(PYVERSION)' -f Dockerfile .;

test-%:
	docker run $(DOCKER_FLAGS) -v $$PWD/$*:/senpy-plugins/ --rm -ti '$(REPO)/$(NAME):$(VERSION)-python$(PYVERSION)' --only-test $(TEST_FLAGS)

test: test-.

clean:
	@docker ps -a | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1;}}' | xargs docker rm 2>/dev/null|| true
	@docker images | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true

run: build
	docker run $(DOCKER_FLAGS) --rm -p 5000:5000 -ti '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)'

.PHONY: test test-% build-% build test test_pip run clean
