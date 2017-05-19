PYVERSIONS=3.5 2.7
PYMAIN=$(firstword $(PYVERSIONS))
NAME=senpy
REPO=gsiupm
VERSION=$(shell git describe --tags --dirty 2>/dev/null)
TARNAME=$(NAME)-$(VERSION).tar.gz 
IMAGENAME=$(REPO)/$(NAME)
IMAGEWTAG=$(IMAGENAME):$(VERSION)
DEVPORT=5000
action="test-${PYMAIN}"
GITHUB_REPO=git@github.com:gsi-upm/senpy.git

KUBE_CA_PEM_FILE=""
KUBE_URL=""
KUBE_TOKEN=""
KUBE_NS=$(NAME)
KUBECTL=docker run --rm -v $(KUBE_CA_PEM_FILE):/tmp/ca.pem -v $$PWD:/tmp/cwd/ -i lachlanevenson/k8s-kubectl --server="$(KUBE_URL)" --token="$(KUBE_TOKEN)" --certificate-authority="/tmp/ca.pem" -n $(KUBE_NAMESPACE)
CI_REGISTRY=docker.io
CI_REGISTRY_USER=gitlab
CI_BUILD_TOKEN=""
CI_COMMIT_REF_NAME=master



all: build run

.FORCE:

version: .FORCE
	@echo $(VERSION) > $(NAME)/VERSION
	@echo $(VERSION)

yapf:
	yapf -i -r $(NAME)
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
	docker build -t '$(IMAGEWTAG)-python$*' --cache-from $(IMAGENAME):python$* -f Dockerfile-$* .;

quick_test: $(addprefix test-,$(PYMAIN))

dev-%:
	@docker start $(NAME)-dev$* || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -p $(DEVPORT):5000 -v $$PWD:/usr/src/app --entrypoint=/bin/bash -ti --name $(NAME)-dev$* '$(IMAGEWTAG)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev$* bash

dev: dev-$(PYMAIN)

test-all: $(addprefix test-,$(PYVERSIONS))

test-%:
	docker run --rm --entrypoint /usr/local/bin/python -w /usr/src/app $(IMAGENAME):python$*  setup.py test

test: test-$(PYMAIN)

dist/$(TARNAME): version
	docker run --rm -ti -v $$PWD:/usr/src/app/ -w /usr/src/app/ python:$(PYMAIN) python setup.py sdist;
	docker run --rm -ti -v $$PWD:/usr/src/app/ -w /usr/src/app/ python:$(PYMAIN) chmod -R a+rwx dist;


sdist: dist/$(TARNAME)

pip_test-%: sdist
	docker run --rm -v $$PWD/dist:/dist/ -ti python:$* pip install /dist/$(TARNAME);

pip_test: $(addprefix pip_test-,$(PYVERSIONS))

clean:
	@docker ps -a | grep $(IMAGENAME) | awk '{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1;}}' | xargs docker rm -v 2>/dev/null|| true
	@docker images | grep $(IMAGENAME) | awk '{ split($$2, vers, "-"); if(vers[0] != "${VERSION}"){ print $$1":"$$2;}}' | xargs docker rmi 2>/dev/null|| true
	@docker stop $(addprefix $(NAME)-dev,$(PYVERSIONS)) 2>/dev/null || true
	@docker rm $(addprefix $(NAME)-dev,$(PYVERSIONS)) 2>/dev/null || true

git_commit:
	git commit -a

git_tag:
	git tag ${VERSION}

git_push:
	git push --tags origin master

pip_upload: pip_test 
	python setup.py sdist upload ;

run-%: build-%
	docker run --rm -p $(DEVPORT):5000 -ti '$(IMAGEWTAG)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

push-latest: $(addprefix push-latest-,$(PYVERSIONS))
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGENAME)'
	docker push '$(IMAGENAME):latest'
	docker push '$(IMAGEWTAG)'

push-latest-%: build-%
	docker tag $(IMAGENAME):$(VERSION)-python$* $(IMAGENAME):python$*
	docker push $(IMAGENAME):$(VERSION)-python$*
	docker push $(IMAGENAME):python$*

push-%: build-%
	docker push $(IMAGENAME):$(VERSION)-python$*

push: $(addprefix push-,$(PYVERSIONS))
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker push  $(IMAGENAME):$(VERSION)

push-github:
	$(eval KEY_FILE := $(shell mktemp))
	@echo "$$GITHUB_DEPLOY_KEY" > $(KEY_FILE)
	@git remote rm github-deploy || true
	git remote add github-deploy $(GITHUB_REPO)
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git push github-deploy $(CI_COMMIT_REF_NAME)
	rm $(KEY_FILE)

ci:
	gitlab-runner exec docker --docker-volumes /var/run/docker.sock:/var/run/docker.sock --env CI_PROJECT_NAME=$(NAME) ${action}

deploy:
	$(KUBECTL) delete -n $(KUBE_NS) secret $(CI_REGISTRY) || true
	@$(KUBECTL) create -n $(NAME) secret docker-registry $(CI_REGISTRY) --docker-server=$(CI_REGISTRY) --docker-username=$(CI_REGISTRY_USER) --docker-email=$(CI_REGISTRY_USER) --docker-password=$(CI_BUILD_TOKEN)
	$(KUBECTL) apply -f /tmp/cwd/k8s/



.PHONY: test test-% test-all build-% build test pip_test run yapf push-main push-% dev ci version .FORCE deploy
