makefiles-remote:
	git remote add makefiles ssh://git@lab.cluster.gsi.dit.upm.es:2200/docs/templates/makefiles.git || true

makefiles-commit:
	git add -f .makefiles
	git commit -m "Updated makefiles from ${NAME}"

makefiles-push: makefiles-remote
	git subtree push --prefix=.makefiles/ makefiles $(NAME)

makefiles-pull: makefiles-remote
	git subtree pull --prefix=.makefiles/ makefiles master --squash

.PHONY:: makefiles-remote makefiles-commit makefiles-push makefiles-pull
