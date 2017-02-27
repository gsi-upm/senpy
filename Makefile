PYVERSIONS=3.5 3.4 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell ./version.sh)
TARNAME=$(NAME)-$(VERSION).tar.gz 
IMAGENAME=$(REPO)/$(NAME):$(VERSION)
TEST_COMMAND=gitlab-runner exec docker --cache-dir=/tmp/gitlabrunner --docker-volumes /tmp/gitlabrunner:/tmp/gitlabrunner --env CI_PROJECT_NAME=$(NAME)

all: build run

FORCE:

version: FORCE
	@echo $(VERSION) > $(NAME)/VERSION
	@echo $(NAME) $(VERSION)

yapf:
	yapf -i -r senpy
	yapf -i -r tests

dev:
	pip install --user pre-commit
	pre-commit install

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS))
	@unlink Dockerfile >/dev/null
	ln -s Dockerfile-$(PYMAIN) Dockerfile

Dockerfile-%: Dockerfile.template
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

quick_build: $(addprefix build-, $(PYMAIN))

build: $(addprefix build-, $(PYVERSIONS))

build-%: Dockerfile-%
	docker build -t '$(IMAGENAME)-python$*' -f Dockerfile-$* .;

quick_test: $(addprefix test-,$(PYMAIN))

test: $(addprefix test-,$(PYVERSIONS))

debug-%:
	@docker start $(NAME)-debug || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -v $$PWD:/usr/src/app --entrypoint=/bin/bash -p 5000:5000 -ti --name $(NAME)-debug '$(IMAGENAME)-python$*'; \
		docker exec -ti $(NAME)-debug pip install -r test-requirements.txt; \
	)\

	docker attach $(NAME)-debug

debug: debug-$(PYMAIN)

test-%:
	$(TEST_COMMAND) test-$*

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
	@docker rmi $(NAME)-debug 2>/dev/null || true

upload_git:
	git commit -a
	git tag ${VERSION}
	git push --tags origin master

pip_upload:
	python setup.py sdist upload ;

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

run-%: build-%
	docker run --rm -p 5000:5000 -ti '$(IMAGENAME)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

.PHONY: test test-% build-% build test pip_test run yapf dev
