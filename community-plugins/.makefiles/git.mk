commit:
	git commit -a

tag:
	git tag ${VERSION}

git-push::
	git push --tags -u origin HEAD

git-pull:
	git pull --all

push-github: ## Push the code to github. You need to set up GITHUB_DEPLOY_KEY
ifeq ($(GITHUB_DEPLOY_KEY),)
else
	$(eval KEY_FILE := "$(shell mktemp)")
	@printf '%b' '$(GITHUB_DEPLOY_KEY)' > $(KEY_FILE)
	@git remote rm github-deploy || true
	git remote add github-deploy $(GITHUB_REPO)
	-@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git fetch github-deploy $(CI_COMMIT_REF_NAME)
	@GIT_SSH_COMMAND="ssh -i $(KEY_FILE)" git push github-deploy HEAD:$(CI_COMMIT_REF_NAME)
	rm $(KEY_FILE)
endif

push:: git-push
pull:: git-pull

.PHONY:: commit tag push git-push git-pull push-github 
