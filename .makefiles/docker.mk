IMAGENAME?=$(NAME)
IMAGEWTAG?=$(IMAGENAME):$(VERSION)

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

login:: docker-login

clean:: docker-clean

docker-info:
	@echo IMAGEWTAG=${IMAGEWTAG}

.PHONY:: docker-login docker-clean login clean
