makefiles-remote:
	git ls-remote --exit-code  makefiles 2> /dev/null || git remote add makefiles ssh://git@lab.cluster.gsi.dit.upm.es:2200/docs/templates/makefiles.git

makefiles-commit: makefiles-remote
	git add -f .makefiles
	git commit -em "Updated makefiles from ${NAME}"

makefiles-push:
	git fetch makefiles $(NAME)
	git subtree push --prefix=.makefiles/ makefiles $(NAME)

makefiles-pull: makefiles-remote
	git subtree pull --prefix=.makefiles/ makefiles master --squash

.PHONY:: makefiles-remote makefiles-commit makefiles-push makefiles-pull
