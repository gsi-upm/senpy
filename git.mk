git_commit:
	git commit -a

git_tag:
	git tag ${VERSION}

git_push:
	git push --tags origin master

push-github: ## Push the code to github. You need to set up HUB_USER and HUB_PASSWORD
	$(eval KEY_FILE := $(shell mktemp))
	@echo "$$GITHUB_DEPLOY_KEY" > $(KEY_FILE)
	@git remote rm github-deploy || true
	git remote add github-deploy $(GITHUB_REPO)
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git fetch github-deploy $(CI_COMMIT_REF_NAME) || true
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git push github-deploy $(CI_COMMIT_REF_NAME)
	rm $(KEY_FILE)

.PHONY:: git_commit git_tag git_push push-github
