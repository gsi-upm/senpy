makefiles-remote:
	@git remote add makefiles ssh://git@lab.cluster.gsi.dit.upm.es:2200/docs/templates/makefiles.git 2>/dev/null || true

makefiles-commit: makefiles-remote
	git add -f .makefiles
	git commit -em "Updated makefiles from ${NAME}"

makefiles-push:
	git subtree push --prefix=.makefiles/ makefiles $(NAME)

makefiles-pull: makefiles-remote
	git subtree pull --prefix=.makefiles/ makefiles master --squash

pull:: makefiles-pull
push:: makefiles-push

.PHONY:: makefiles-remote makefiles-commit makefiles-push makefiles-pull pull push
