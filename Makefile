PYVERSIONS=3.4 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell cat $(NAME)/VERSION)


all: build run

yapf:
	yapf -i -r senpy
	yapf -i -r tests

dev:
	pip install --user pre-commit
	pre-commit install

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS))
	ln -s Dockerfile-$(PYMAIN) Dockerfile

Dockerfile-%: Dockerfile.template
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

build: $(addprefix build-, $(PYMAIN))

buildall: $(addprefix build-, $(PYVERSIONS))

build-%: Dockerfile-%
	docker build -t '$(REPO)/$(NAME):$(VERSION)-python$*' -f Dockerfile-$* .;

build-debug-%:
	docker build -t '$(NAME)-debug' -f Dockerfile-debug-$* .;

test: $(addprefix test-,$(PYMAIN))

testall: $(addprefix test-,$(PYVERSIONS))

debug-%: build-debug-%
	docker run --rm -w /usr/src/app/ -v $$PWD:/usr/src/app --entrypoint=/bin/bash -ti $(NAME)-debug ;

debug: debug-$(PYMAIN)

test-%: build-%
	docker run --rm -w /usr/src/app/ --entrypoint=/usr/local/bin/python -ti '$(REPO)/$(NAME):$(VERSION)-python$*' setup.py test --addopts "-vvv -s" ;

dist/$(NAME)-$(VERSION).tar.gz:
	docker run --rm -ti -v $$PWD:/usr/src/app/ -w /usr/src/app/ python:$(PYMAIN) python setup.py sdist;

sdist: dist/$(NAME)-$(VERSION).tar.gz

pip_test-%: sdist
	docker run --rm -v $$PWD/dist:/dist/ -ti python:$* pip install /dist/$(NAME)-$(VERSION).tar.gz ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

upload-%: test-%
	docker push '$(REPO)/$(NAME):$(VERSION)-python$*'

upload: testall $(addprefix upload-,$(PYVERSIONS))
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)' '$(REPO)/$(NAME):$(VERSION)'
	docker tag '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)' '$(REPO)/$(NAME)'
	docker push '$(REPO)/$(NAME):$(VERSION)'

clean:
	@docker ps -a | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1;}}' | xargs docker rm 2>/dev/null|| true
	@docker images | awk '/$(REPO)\/$(NAME)/{ split($$2, vers, "-"); if(vers[1] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true
	@docker rmi $(NAME)-debug 2>/dev/null || true

upload_git:
	git commit -a
	git tag ${VERSION}
	git push --tags origin master

pip_upload:
	python setup.py sdist upload ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

run: build
	docker run --rm -p 5000:5000 -ti '$(REPO)/$(NAME):$(VERSION)-python$(PYMAIN)'

.PHONY: test test-% build-% build test test_pip run yapf dev
