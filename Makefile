NAME=senpy
VERSION=$(shell git describe --tags --dirty 2>/dev/null)
GITHUB_REPO=git@github.com:gsi-upm/senpy.git

IMAGENAME=gsiupm/senpy
IMAGEWTAG=$(IMAGENAME):$(VERSION)

PYVERSIONS=3.5 2.7
PYMAIN=$(firstword $(PYVERSIONS))

DEVPORT=5000

TARNAME=$(NAME)-$(VERSION).tar.gz 
action="test-${PYMAIN}"
GITHUB_REPO=git@github.com:gsi-upm/senpy.git

KUBE_CA_PEM_FILE=""
KUBE_URL=""
KUBE_TOKEN=""
KUBE_NAMESPACE=$(NAME)
KUBECTL=docker run --rm -v $(KUBE_CA_PEM_FILE):/tmp/ca.pem -v $$PWD:/tmp/cwd/ -i lachlanevenson/k8s-kubectl --server="$(KUBE_URL)" --token="$(KUBE_TOKEN)" --certificate-authority="/tmp/ca.pem" -n $(KUBE_NAMESPACE)
CI_COMMIT_REF_NAME=master

help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/\(.*:\)[^#]*##\s*\(.*\)/\1\t\2/' | column -t -s "	"

config:  ## Load config from the environment. You should run it once in every session before other tasks. Run: eval $(make config)
	@echo ". ../.env || true;"
	@awk '{ print "export " $$0}' .env
	@echo "# Please, run: "
	@echo "# eval \$$(make config)"
# If you need to run a command on the key/value pairs, use this:
# @awk '{ split($$0, a, "="); "echo " a[2] " | base64 -w 0" |& getline b64; print "export " a[1] "=" a[2]; print "export " a[1] "_BASE64=" b64}' .env

quick_build: $(addprefix build-, $(PYMAIN))

build: $(addprefix build-, $(PYVERSIONS)) ## Build all images / python versions

build-%: version Dockerfile-%  ## Build a specific version (e.g. build-2.7)
	docker build -t '$(IMAGEWTAG)-python$*' --cache-from $(IMAGENAME):python$* -f Dockerfile-$* .;

quick_test: test-$(PYMAIN)

dev-%: ## Launch a specific development environment using docker (e.g. dev-2.7)
	@docker start $(NAME)-dev$* || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -p $(DEVPORT):5000 -v $$PWD:/usr/src/app --entrypoint=/bin/bash -ti --name $(NAME)-dev$* '$(IMAGEWTAG)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev$* bash

dev: dev-$(PYMAIN) ## Launch a development environment using docker, using the default python version

test-%: ## Run setup.py from in an isolated container, built from the base image. (e.g. test-2.7)
# This speeds tests up because the image has most (if not all) of the dependencies already.
	docker rm $(NAME)-test-$* || true
	docker create -ti --name $(NAME)-test-$* --entrypoint="" -w /usr/src/app/ $(IMAGENAME):python$* python setup.py test
	docker cp . $(NAME)-test-$*:/usr/src/app
	docker start -a $(NAME)-test-$*

test: $(addprefix test-,$(PYVERSIONS)) ## Run the tests with the main python version

run-%: build-%
	docker run --rm -p $(DEVPORT):5000 -ti '$(IMAGEWTAG)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)


#
# Deployment and advanced features
# 


deploy: ## Deploy to kubernetes using the credentials in KUBE_CA_PEM_FILE (or KUBE_CA_BUNDLE ) and TOKEN
	@cat k8s/* | envsubst | $(KUBECTL) apply -f -

deploy-check: ## Get the deployed configuration.
	@$(KUBECTL) get deploy,pods,svc,ingress

login: ## Log in to the registry. It will only be used in the server, or when running a CI task locally (if CI_BUILD_TOKEN is set).
ifeq ($(CI_BUILD_TOKEN),)
	@echo "Not logging in to the docker registry" "$(CI_REGISTRY)"
else
	docker login -u gitlab-ci-token -p $(CI_BUILD_TOKEN) $(CI_REGISTRY)
endif
ifeq ($(HUB_USER),)
	@echo "Not logging in to global the docker registry"
	docker login -u $(HUB_USER) -p $(HUB_PASSWORD)
else
endif

.FORCE:

version: .FORCE
	@echo $(VERSION) > $(NAME)/VERSION
	@echo $(VERSION)

yapf: ## Format python code
	yapf -i -r $(NAME)
	yapf -i -r tests

init: ## Init pre-commit hooks (i.e. enforcing format checking before allowing a commit)
	pip install --user pre-commit
	pre-commit install

dockerfiles: $(addprefix Dockerfile-,$(PYVERSIONS)) ## Generate dockerfiles for each python version
	@unlink Dockerfile >/dev/null
	ln -s Dockerfile-$(PYMAIN) Dockerfile

Dockerfile-%: Dockerfile.template  ## Generate a specific dockerfile (e.g. Dockerfile-2.7)
	sed "s/{{PYVERSION}}/$*/" Dockerfile.template > Dockerfile-$*

dist/$(TARNAME): version
	python setup.py sdist;

sdist: dist/$(TARNAME) ## Generate the distribution file (wheel)

pip_test-%: sdist ## Test the distribution file using pip install and a specific python version (e.g. pip_test-2.7)
	docker run --rm -v $$PWD/dist:/dist/ python:$* pip install /dist/$(TARNAME);

pip_test: $(addprefix pip_test-,$(PYVERSIONS)) ## Test pip installation with the main python version

pip_upload: pip_test  ## Upload package to pip
	python setup.py sdist upload ;

clean: ## Clean older docker images and containers related to this project and dev environments
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

quick_build: $(addprefix build-, $(PYMAIN))

build: $(addprefix build-, $(PYVERSIONS)) ## Build all images / python versions

build-%: version Dockerfile-%  ## Build a specific version (e.g. build-2.7)
	docker build -t '$(IMAGEWTAG)-python$*' --cache-from $(IMAGENAME):python$* -f Dockerfile-$* .;

quick_test: test-$(PYMAIN)

dev-%: ## Launch a specific development environment using docker (e.g. dev-2.7)
	@docker start $(NAME)-dev$* || (\
		$(MAKE) build-$*; \
		docker run -d -w /usr/src/app/ -p $(DEVPORT):5000 -v $$PWD:/usr/src/app --entrypoint=/bin/bash -ti --name $(NAME)-dev$* '$(IMAGEWTAG)-python$*'; \
	)\

	docker exec -ti $(NAME)-dev$* bash

dev: dev-$(PYMAIN) ## Launch a development environment using docker, using the default python version

test-%: ## Run setup.py from in an isolated container, built from the base image. (e.g. test-2.7)
# This speeds tests up because the image has most (if not all) of the dependencies already.
	docker rm $(NAME)-test-$* || true
	docker create -ti --name $(NAME)-test-$* --entrypoint="" -w /usr/src/app/ $(IMAGENAME):python$* python setup.py test
	docker cp . $(NAME)-test-$*:/usr/src/app
	docker start -a $(NAME)-test-$*

test: $(addprefix test-,$(PYVERSIONS)) ## Run the tests with the main python version

run-%: build-%
	docker run --rm -p $(DEVPORT):5000 -ti '$(IMAGEWTAG)-python$(PYMAIN)' --default-plugins

run: run-$(PYMAIN)

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

push: $(addprefix push-,$(PYVERSIONS)) ## Push an image with the current version for every python version
	docker tag '$(IMAGEWTAG)-python$(PYMAIN)' '$(IMAGEWTAG)'
	docker push  $(IMAGENAME):$(VERSION)

push-github: ## Push the code to github. You need to set up HUB_USER and HUB_PASSWORD
	$(eval KEY_FILE := $(shell mktemp))
	@echo "$$GITHUB_DEPLOY_KEY" > $(KEY_FILE)
	@git remote rm github-deploy || true
	git remote add github-deploy $(GITHUB_REPO)
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git fetch github-deploy $(CI_COMMIT_REF_NAME) || true
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git push github-deploy $(CI_COMMIT_REF_NAME)
	rm $(KEY_FILE)

ci:  ## Run a task using gitlab-runner. Only use to debug problems in the CI pipeline
	gitlab-runner exec shell --builds-dir '.builds' --env CI_PROJECT_NAME=$(NAME) ${action}


.PHONY: test test-% test-all build-% build test pip_test run yapf push-main push-% dev ci version .FORCE deploy
