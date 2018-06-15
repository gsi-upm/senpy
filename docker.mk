ifndef IMAGENAME
	ifdef CI_REGISTRY_IMAGE
		IMAGENAME=$(CI_REGISTRY_IMAGE)
	else
		IMAGENAME=$(NAME)
	endif
endif

IMAGEWTAG?=$(IMAGENAME):$(VERSION)
DOCKER_FLAGS?=$(-ti)
DOCKER_CMD?=

docker-login: ## Log in to the registry. It will only be used in the server, or when running a CI task locally (if CI_BUILD_TOKEN is set).
ifeq ($(CI_BUILD_TOKEN),)
	@echo "Not logging in to the docker registry" "$(CI_REGISTRY)"
else
	@docker login -u gitlab-ci-token -p $(CI_BUILD_TOKEN) $(CI_REGISTRY)
endif
ifeq ($(HUB_USER),)
	@echo "Not logging in to global the docker registry"
else
	@docker login -u $(HUB_USER) -p $(HUB_PASSWORD)
endif

docker-clean: ## Remove docker credentials
ifeq ($(HUB_USER),)
else
	@docker logout
endif

docker-run: ## Build a generic docker image
	docker run $(DOCKER_FLAGS) $(IMAGEWTAG) $(DOCKER_CMD)

docker-build: ## Build a generic docker image
	docker build . -t $(IMAGEWTAG)

docker-push: docker-login ## Push a generic docker image
	docker push $(IMAGEWTAG)

docker-latest-push: docker-login ## Push the latest image
	docker tag $(IMAGEWTAG) $(IMAGENAME)
	docker push $(IMAGENAME)

login:: docker-login

clean:: docker-clean

docker-info:
	@echo IMAGEWTAG=${IMAGEWTAG}

.PHONY:: docker-login docker-clean login clean
