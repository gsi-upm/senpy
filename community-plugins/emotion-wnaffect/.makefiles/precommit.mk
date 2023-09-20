init: ## Init pre-commit hooks (i.e. enforcing format checking before allowing a commit)
	pip install --user pre-commit
	pre-commit install

.PHONY:: init
